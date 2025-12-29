#include <iostream>
#include <memory>
#include <string>
#include <map>
#include <mutex>
#include <fstream>
#include <sstream>
#include <vector>

#include <grpcpp/grpcpp.h>
#include "kv_store.grpc.pb.h"

using grpc::Server;
using grpc::ServerBuilder;
using grpc::ServerContext;
using grpc::Status;
using kvstore::KeyValueStore;
using kvstore::PutRequest;
using kvstore::PutResponse;
using kvstore::GetRequest;
using kvstore::GetResponse;
using kvstore::DeleteRequest;
using kvstore::DeleteResponse;
using kvstore::Empty;
using kvstore::KeyListResponse;

const std::string DB_FILE = "/data/kv_store_data.log";

struct Entry {
    std::string value;
    int64_t version;
};

class KeyValueStoreImpl final : public KeyValueStore::Service {
    std::map<std::string, Entry> kv_map_;
    std::mutex mutex_;

    // Logger
    void LogToDisk(const std::string& action, const std::string& key, const std::string& value, int64_t version) {
        std::ofstream outfile;
        outfile.open(DB_FILE, std::ios::app);
        if (outfile.is_open()) {

            outfile << action << "|" << key << "|" << value << "|" << version << "\n";
            outfile.close();
        }
    }

public:
    KeyValueStoreImpl() {
        std::ifstream infile(DB_FILE);
        std::string line;
        
        std::cout << "[Server] Recovering data..." << std::endl;
        
        while (std::getline(infile, line)) {
            std::stringstream ss(line);
            std::string segment;
            std::vector<std::string> parts;

            while (std::getline(ss, segment, '|')) {
                parts.push_back(segment);
            }

            if (parts.size() >= 2) {
                std::string action = parts[0];
                std::string key = parts[1];
                
                if (action == "DELETE") {
                    kv_map_.erase(key);
                } 
                else if ((action == "PUT" || action == "UPDATE") && parts.size() >= 4) {
                    // Load Value and Version
                    std::string val = parts[2];
                    int64_t ver = std::stoll(parts[3]); // Convert string to int64
                    
                    // LWW Logic during recovery
                    if (kv_map_.find(key) == kv_map_.end() || ver >= kv_map_[key].version) {
                        kv_map_[key] = {val, ver};
                    }
                }
            }
        }
    }

    Status Put(ServerContext* context, const PutRequest* request, PutResponse* response) override {
        std::lock_guard<std::mutex> lock(mutex_);
        
        if (kv_map_.find(request->key()) != kv_map_.end()) {
            if (kv_map_[request->key()].version > request->version()) {
                response->set_success(true); 
                response->set_message("Ignored: Stale version.");
                return Status::OK;
            }
        }

        // Save to Disk & RAM
        LogToDisk("PUT", request->key(), request->value(), request->version());
        kv_map_[request->key()] = {request->value(), request->version()};
        
        response->set_success(true);
        response->set_message("Saved.");
        return Status::OK;
    }

    // Update is just an alias for Put in LWW systems
    Status Update(ServerContext* context, const PutRequest* request, PutResponse* response) override {
        return Put(context, request, response);
    }

    Status Get(ServerContext* context, const GetRequest* request, GetResponse* response) override {
        std::lock_guard<std::mutex> lock(mutex_);
        
        auto it = kv_map_.find(request->key());
        if (it != kv_map_.end()) {
            response->set_value(it->second.value);
            response->set_version(it->second.version); // Return the version
            response->set_found(true);
        } else {
            response->set_found(false);
        }
        return Status::OK;
    }

    Status Delete(ServerContext* context, const DeleteRequest* request, DeleteResponse* response) override {
        std::lock_guard<std::mutex> lock(mutex_);
        if (kv_map_.erase(request->key())) {
            LogToDisk("DELETE", request->key(), "", 0);
            response->set_success(true);
            response->set_message("Deleted.");
        } else {
            response->set_success(false);
            response->set_message("Not found.");
        }
        return Status::OK;
    }

    Status ListKeys(ServerContext* context, const Empty* request, KeyListResponse* response) override {
        std::lock_guard<std::mutex> lock(mutex_);
        for (const auto& pair : kv_map_) {
            response->add_keys(pair.first);
        }
        return Status::OK;
    }
};

void RunServer() {
    std::string server_address("0.0.0.0:50051");
    KeyValueStoreImpl service;
    ServerBuilder builder;
    builder.AddListeningPort(server_address, grpc::InsecureServerCredentials());
    builder.RegisterService(&service);
    std::unique_ptr<Server> server(builder.BuildAndStart());
    std::cout << "Server listening on " << server_address << std::endl;
    server->Wait();
}

int main(int argc, char** argv) {
    RunServer();
    return 0;
}