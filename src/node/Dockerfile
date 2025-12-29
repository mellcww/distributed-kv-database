# Pick a base OS (Ubuntu 22.04 is stable and has gRPC packages)
FROM ubuntu:22.04

# Install the C++ Compiler and gRPC libraries
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    build-essential \
    cmake \
    git \
    pkg-config \
    libgrpc++-dev \
    libprotobuf-dev \
    protobuf-compiler-grpc \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Copy the Protobuf definitions
COPY protos /app/protos

# Copy the C++ Source Code
COPY src/node /app/src/node

# This ensures the .pb.cc files match the Docker container's library version
RUN protoc -I=protos --cpp_out=src/node --grpc_out=src/node --plugin=protoc-gen-grpc=`which grpc_cpp_plugin` protos/kv_store.proto

# Build the Server
WORKDIR /app/src/node/build
RUN cmake .. && make
RUN mkdir -p /data

# Open the Port
EXPOSE 50051

# The command to run when the container starts
CMD ["./kv_server"]