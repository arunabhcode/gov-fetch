#!/bin/bash
# Script to detect if NVIDIA GPU is available and select the appropriate Docker Compose profile

# Check if nvidia-smi is available and can connect to a GPU
if command -v nvidia-smi &> /dev/null && nvidia-smi &> /dev/null; then
    export COMPOSE_PROFILES="gpu"
else
    export COMPOSE_PROFILES="cpu"
fi 