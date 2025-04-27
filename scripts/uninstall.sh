#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status messages
print_status() {
    echo -e "${GREEN}[+] $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[!] $1${NC}"
}

print_error() {
    echo -e "${RED}[-] $1${NC}"
}

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root (use sudo)"
    exit 1
fi

# Installation directory
INSTALL_DIR="/opt/gov-fetch"

# Stop and disable service if it exists
if systemctl is-active --quiet gov-fetch; then
    print_status "Stopping Gov Fetch service..."
    systemctl stop gov-fetch
fi

if systemctl is-enabled --quiet gov-fetch 2>/dev/null; then
    print_status "Disabling Gov Fetch service..."
    systemctl disable gov-fetch
fi

# Remove systemd service file
if [ -f "/etc/systemd/system/gov-fetch.service" ]; then
    print_status "Removing systemd service file..."
    rm -f /etc/systemd/system/gov-fetch.service
    systemctl daemon-reload
fi

# Remove docker containers and images
print_status "Cleaning up Docker resources..."
if docker compose -f "$INSTALL_DIR/docker-compose.yml" &>/dev/null; then
    docker compose -f "$INSTALL_DIR/docker-compose.yml" down --volumes --remove-orphans
fi

# Optional: remove the Docker image
if docker image inspect gov/fetch &>/dev/null; then
    print_status "Removing Gov Fetch Docker image..."
    docker image rm gov/fetch
fi

# Remove installation directory
if [ -d "$INSTALL_DIR" ]; then
    print_status "Removing installation directory..."
    rm -rf "$INSTALL_DIR"
fi

print_status "Gov Fetch has been successfully uninstalled." 