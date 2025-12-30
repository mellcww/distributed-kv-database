# Distributed KV Database: A Scalable MultiNode High-Performance Cluster

This project is a resilient, sharded key-value store engineered with a C++17 gRPC core and a Python-based consistent hashing orchestrator. It was built to demonstrate full-lifecycle distributed systems engineering: from low-level systems programming to cross-architecture cloud deployment on AWS.

<img width="1281" height="908" alt="Screenshot 2025-12-29 at 8 28 37 PM" src="https://github.com/user-attachments/assets/3cc86fb4-2279-4e3d-8af2-2c42d227045f" />
<img width="1382" height="832" alt="Screenshot_2025-12-29_at_3 04 56_AM" src="https://github.com/user-attachments/assets/2c9209f4-31a7-4744-ac39-31b7c4a9387f" />
<img width="1136" height="880" alt="Screenshot_2025-12-29_at_3 04 33_AM" src="https://github.com/user-attachments/assets/1fd1fb00-54dc-4978-ba9e-2c672d64c91b" />

## Technical Architecture

### 1. High-Performance Storage Core (C++17 & gRPC)
The storage layer is a native C++ implementation designed for maximum throughput and minimal overhead:
- **Binary Efficiency via Protocol Buffers:** By bypassing human-readable formats like JSON, the system utilizes Protobuf for binary serialization. This resulted in approximately 3x faster transmission speeds and a significantly reduced memory footprint during high-concurrency operations.
- **RPC vs REST Implementation:** The architecture implements a dual-protocol stack. The external client interface is a RESTful API for ease of integration, while all internal cluster communication is handled via gRPC (HTTP/2). This enables persistent connections, header compression, and multiplexing, eliminating the head-of-line blocking found in traditional HTTP 1.1 setups.
- **Concurrency and Parallelism:** Each storage node leverages C++ multithreading to handle simultaneous gRPC requests. By isolating state management within each process, the system prevents global lock contention, allowing for true parallelism across the CPU cores of the host machine.



### 2. Scalable Sharding Strategy (Consistent Hashing)
The system solves the "K-node re-sharding" trap, where adding a single server typically requires remapping nearly every key in a database—through a sophisticated Consistent Hash Ring:
- **Minimal Data Movement:** By mapping both nodes and keys onto a 360-degree virtual ring, the system ensures that adding or removing a node only requires re-mapping 1/n of the total keys. This makes the cluster horizontally scalable with near-zero downtime.
- **System Design Patterns:** The implementation follows the Gateway Pattern, where a single Python-based entry point handles the complex hashing logic and request routing, keeping the C++ storage shards hyper-optimized for I/O operations.



## Production Engineering & AWS Deployment

### 1. The Cross-Architecture Build Pipeline
A major engineering hurdle was the architecture mismatch between the development environment (Apple Silicon / ARM64) and the production cloud (AWS Intel / AMD64).
- **Multi-Platform Dockerization:** Utilizing docker buildx, the C++ binaries were cross-compiled specifically for the linux/amd64 target. This process overcame the manifest reconciliation issues common in cross-platform deployments.
- **Docker Orchestration:** 8 containers (1 Gateway + 7 Nodes) are orchestrated inside a private Docker bridge network. This allows for internal service discovery via container hostnames, keeping gRPC traffic completely isolated from the public internet.

### 2. Cloud-Native Scalability (AWS)
Built for the AWS Ecosystem, the system utilizes modern cloud primitives for deployment and security:
- **Registry Management:** Integrated with AWS Elastic Container Registry (ECR) for private image hosting, managing the full lifecycle of automated pushes and remote manifest reconciliation.
- **Network Security:** Configured AWS Security Groups to expose only the necessary Gateway port (8080) for the REST API, while maintaining a hardened, private internal network for gRPC node communication.

## Benchmarking & Monitoring

- **Multi-Threaded Stress Test:** The benchmarking suite utilizes concurrent.futures to simulate over 100 parallel users. This validates the system's ability to maintain data integrity and routing accuracy under extreme concurrency.
- **Real-Time Visualization:** A custom dashboard provides a live window into the cluster, visualizing node heartbeats, live key distribution, and sharding metadata.

## System Evolution and Performance Metrics

### Optimization Results: 136 to 417 Requests Per Second
During initial benchmarking, the system used standard JSON serialization over HTTP/1.1 for inter-node communication, peaking at approximately 136 requests per second under heavy load.

By re-engineering the internal backbone to use gRPC and Protocol Buffers, the system achieved a significant performance breakthrough:
- **Throughput:** Increased from 136 req/s to 417 req/s (a 302% improvement).
- **Latency Reduction:** Binary serialization reduced payload sizes by over 60%, drastically lowering the I/O wait times for the orchestrator.
- **Connection Efficiency:** The move to HTTP/2 allowed the gateway to maintain a single multiplexed connection to each C++ shard, removing the TCP handshake overhead associated with traditional REST calls.
<img width="434" height="122" alt="Screenshot_2025-12-29_at_4 23 39_PM" src="https://github.com/user-attachments/assets/29cb8e9a-bda5-4433-ae44-95c1b1f61517" />


## Project Structure

- `/src/node`: C++17 gRPC storage engine source code.
- `/src/gateway`: Python 3.9 Consistent Hashing orchestrator and REST API.
- `/protos`: Strictly typed Protobuf definitions for cross-language IPC.
- `dashboard.html`: Real-time monitoring UI using the Fetch API.
- `stress_test.py`: Multi-threaded performance benchmarking tool.

## How To Use

### Launch the Cluster
Ensure you have Docker and Docker Compose installed.

```bash
# Clone the repository
git clone [https://github.com/mellcww/distributed-kv-database.git](https://github.com/mellcww/distributed-kv-database.git)
cd distributed-kv-database

# Spin up 7 storage nodes and 1 gateway
docker compose up --build -d
```

### Verify and Monitor

Check Status: Run docker ps to ensure all 8 containers are "Up".
Dashboard: Open dashboard.html in any browser to see the live hash ring and key distribution.

### Run Benchmarks

Use the multi-threaded stress test to validate throughput:

```bash
# Simulates 2000 parallel users
python3 stress_test.py
```

## Contact

For any inquiries or suggestions, feel free to reach out:

- Email: akiradev02@icloud.com

#
Project Link: [distributed-kv-database](https://github.com/mellcww/distributed-kv-database)
