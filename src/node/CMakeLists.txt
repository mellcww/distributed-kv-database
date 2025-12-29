cmake_minimum_required(VERSION 3.15)
project(KeyValueStore)

set(CMAKE_CXX_STANDARD 17)

# Use PkgConfig to find the libraries (Standard for Linux)
find_package(PkgConfig REQUIRED)
pkg_check_modules(GRPC REQUIRED grpc++ grpc)
pkg_check_modules(PROTOBUF REQUIRED protobuf)

# Include the headers
include_directories(${GRPC_INCLUDE_DIRS} ${PROTOBUF_INCLUDE_DIRS})
include_directories(${CMAKE_CURRENT_BINARY_DIR})

# Define the source files
set(SOURCES
    main.cpp
    kv_store.pb.cc
    kv_store.grpc.pb.cc
)

# Create the Executable
add_executable(kv_server ${SOURCES})

# Link the libraries
target_link_libraries(kv_server
    ${GRPC_LIBRARIES}
    ${PROTOBUF_LIBRARIES}

    grpc++_reflection
    dl
)