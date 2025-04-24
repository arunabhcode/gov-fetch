#!/bin/bash
# Script to detect if NVIDIA GPU is available and select the appropriate Docker Compose profile

# Check if nvidia-smi is available and can connect to a GPU
if command -v nvidia-smi &> /dev/null && nvidia-smi &> /dev/null; then
    echo "COMPOSE_PROFILES=gpu"
else
    echo "COMPOSE_PROFILES=cpu"
fi 