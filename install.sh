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

# Get the directory of the script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="/opt/gov-fetch"

print_status "Building Gov Fetch Docker image..."
cd "$SCRIPT_DIR"
docker build -t gov/fetch .

print_status "Creating installation directory at $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"

print_status "Copying files to $INSTALL_DIR..."
cp -r "$SCRIPT_DIR"/* "$INSTALL_DIR"
chmod +x "$INSTALL_DIR/detect-gpu.sh"

# Detect if running with GPU
if command -v nvidia-smi &> /dev/null && nvidia-smi &> /dev/null; then
    print_status "NVIDIA GPU detected - service will use GPU profile"
else
    print_warning "No NVIDIA GPU detected - service will use CPU profile"
fi

print_status "Setting up systemd service..."
cp "$SCRIPT_DIR/gov-fetch.service" /etc/systemd/system/

# Reload systemd, enable and start service
print_status "Enabling and starting Gov Fetch service..."
systemctl daemon-reload
systemctl enable gov-fetch
systemctl start gov-fetch

print_status "Installation complete!"
print_status "Service status: $(systemctl is-active gov-fetch)"
print_status "Check logs with: journalctl -u gov-fetch -f"


