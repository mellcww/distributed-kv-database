import os
import grpc
import time
from flask import Flask, jsonify, request
import kv_store_pb2
import kv_store_pb2_grpc
from hash_ring import ConsistentHashRing

app = Flask(__name__)

# --- CORS Headers ---
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# --- CONFIG ---
node_list_str = os.getenv('STORAGE_NODE_ADDRESSES', 'localhost:50051')
ALL_NODES = node_list_str.split(',')
ring = ConsistentHashRing(nodes=ALL_NODES, replication_factor=2)

def get_grpc_stub(node_address):
    return kv_store_pb2_grpc.KeyValueStoreStub(grpc.insecure_channel(node_address))

# --- HELPERS ---
def safe_grpc_call(node, func, *args):
    try:
        stub = get_grpc_stub(node)
        return func(stub, *args), None
    except grpc.RpcError as e:
        return None, f"Unreachable"

# --- 1. PUT (With Timestamp) ---
@app.route('/put', methods=['POST'])
def put_kv():
    data = request.json
    key = data['key']
    val = data['value']
    
    # Generate timestamp (Nano-seconds)
    version = time.time_ns()

    target_nodes = ring.get_nodes(key)
    
    # Send Key + Value + Version to all replicas
    req = kv_store_pb2.PutRequest(key=key, value=val, version=version)
    
    success_count = 0
    for node in target_nodes:
        response, err = safe_grpc_call(node, lambda s, r: s.Put(r), req)
        if response and response.success:
            success_count += 1

    if success_count == 0:
        return jsonify({"error": "Failed"}), 500

    return jsonify({"message": f"Saved", "version": version, "targets": target_nodes})

# --- 2. GET (With Read Repair) ---
@app.route('/get/<key>', methods=['GET'])
def get_kv(key):
    target_nodes = ring.get_nodes(key)
    
    # 1. Gather responses from ALL replicas
    responses = []
    for node in target_nodes:
        req = kv_store_pb2.GetRequest(key=key)
        res, err = safe_grpc_call(node, lambda s, r: s.Get(r), req)
        if res and res.found:
            responses.append({
                "node": node,
                "value": res.value,
                "version": res.version
            })

    if not responses:
        return jsonify({"error": "Key not found"}), 404

    # 2. Find the "Winning" (Newest) Version
    winner = max(responses, key=lambda x: x['version'])
    
    # 3. Detect & Repair Stale Nodes
    read_repair_triggered = False
    for r in responses:
        if r['version'] < winner['version']:
            print(f"⚠️ REPAIRING {r['node']}: Old={r['version']} -> New={winner['version']}")
            # Send the winner data to the loser node
            repair_req = kv_store_pb2.PutRequest(
                key=key, value=winner['value'], version=winner['version']
            )
            safe_grpc_call(r['node'], lambda s, req: s.Put(req), repair_req)
            read_repair_triggered = True

    return jsonify({
        "key": key,
        "value": winner['value'],
        "version": winner['version'],
        "source": winner['node'],
        "repaired": read_repair_triggered
    })

# --- MAP & DELETE (Standard) ---
@app.route('/map', methods=['GET'])
def get_cluster_map():
    state = {}
    for node in ALL_NODES:
        try:
            stub = get_grpc_stub(node)
            res = stub.ListKeys(kv_store_pb2.Empty())
            state[node] = {"status": "Online", "keys": [k for k in res.keys]}
        except:
            state[node] = {"status": "Offline"}
    return jsonify(state)

@app.route('/delete/<key>', methods=['DELETE'])
def delete_kv(key):

    target_nodes = ring.get_nodes(key)
    success = 0
    req = kv_store_pb2.DeleteRequest(key=key)
    for node in target_nodes:
        res, _ = safe_grpc_call(node, lambda s, r: s.Delete(r), req)
        if res and res.success: success += 1
    return jsonify({"deleted_from": success})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)