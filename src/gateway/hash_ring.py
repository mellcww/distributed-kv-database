import hashlib
import bisect

class ConsistentHashRing:
    def __init__(self, nodes=None, replication_factor=2):
        self.replication_factor = replication_factor
        self.ring = {}
        self.sorted_keys = []

        if nodes:
            for node in nodes:
                self.add_node(node)

    def _hash(self, key):
        # Returns a stable hash (MD5) as an integer
        return int(hashlib.md5(key.encode('utf-8')).hexdigest(), 16)

    def add_node(self, node):
        # Adds a node to the ring
        key = self._hash(node)
        self.ring[key] = node
        bisect.insort(self.sorted_keys, key)

    def remove_node(self, node):
        # Removes a node from the ring
        key = self._hash(node)
        if key in self.ring:
            del self.ring[key]
            self.sorted_keys.remove(key)

    def get_nodes(self, key_string):
        # Returns a list of nodes responsible for the key.
        # The first node is the Primary. The others are Replicas.
        if not self.ring:
            return []

        hash_val = self._hash(key_string)
        
        # Binary Search: Find the first node position >= hash_val
        idx = bisect.bisect(self.sorted_keys, hash_val)
        
        # If we went past the end, wrap around to the start (Circle)
        if idx == len(self.sorted_keys):
            idx = 0

        # Collect the primary node and its neighbors (Replicas)
        distinct_nodes = []
        iter_count = 0
        total_nodes = len(self.sorted_keys)
        
        while len(distinct_nodes) < self.replication_factor and iter_count < total_nodes:
            node_key = self.sorted_keys[idx]
            node = self.ring[node_key]
            
            if node not in distinct_nodes:
                distinct_nodes.append(node)
            
            # Move to next node (Circle logic)
            idx = (idx + 1) % total_nodes
            iter_count += 1
            
        return distinct_nodes