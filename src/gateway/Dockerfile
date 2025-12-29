# Start with your existing base
FROM python:3.9-slim

WORKDIR /app

# Install dependencies (Added gunicorn)
RUN pip install --no-cache-dir --default-timeout=100 grpcio grpcio-tools flask gunicorn

# Copy files
COPY protos /app/protos
COPY src/gateway /app/src/gateway

# Generate gRPC code
RUN python3 -m grpc_tools.protoc -I protos \
    --python_out=src/gateway \
    --grpc_python_out=src/gateway \
    protos/kv_store.proto

# Environment setup
ENV PYTHONPATH="${PYTHONPATH}:/app/src/gateway"
EXPOSE 8080

# Run gunicorn
CMD ["gunicorn", "--workers", "4", "--threads", "2", "--bind", "0.0.0.0:8080", "--chdir", "src/gateway", "app:app"]