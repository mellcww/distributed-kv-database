import requests
import concurrent.futures
import time
import random

# CONFIG
NUM_REQUESTS = 2000   # How many total requests to send
CONCURRENT_USERS = 100 # How many threads running at once
GATEWAY_URL = "http://51.20.142.27:8080"

def send_request(i):
    key = f"user_{random.randint(1, 1000)}" # Random keys 1-1000
    value = f"data_{i}"
    
    start = time.time()
    try:
        # 50% chance of Write, 50% chance of Read
        if random.random() > 0.5:
            resp = requests.post(f"{GATEWAY_URL}/put", json={"key": key, "value": value}, timeout=2)
            action = "WRITE"
        else:
            resp = requests.get(f"{GATEWAY_URL}/get/{key}", timeout=2)
            action = "READ "
            
        latency = (time.time() - start) * 1000 # ms
        return f"[{action}] {resp.status_code} | {latency:.2f}ms"
        
    except Exception as e:
        return f"[ERROR] {str(e)}"

def run_stress_test():
    print(f"Starting Stress Test: {NUM_REQUESTS} requests with {CONCURRENT_USERS} users...")
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_USERS) as executor:
        results = list(executor.map(send_request, range(NUM_REQUESTS)))

    total_time = time.time() - start_time
    print(f"\n✅ Finished in {total_time:.2f} seconds")
    print(f"📊 Throughput: {NUM_REQUESTS / total_time:.2f} Requests/Second")
    
    # Count Errors
    errors = [r for r in results if "ERROR" in r or "500" in r or "503" in r]
    print(f"Errors: {len(errors)}")

if __name__ == "__main__":
    run_stress_test()