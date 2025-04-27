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
# Copy specific necessary files and the scripts directory
cp "$SCRIPT_DIR/docker-compose.yml" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/Dockerfile" "$INSTALL_DIR/"
cp -r "$SCRIPT_DIR/src" "$INSTALL_DIR/"
# Ensure the scripts directory exists before copying into it
mkdir -p "$INSTALL_DIR/scripts"
cp -r "$SCRIPT_DIR/scripts"/* "$INSTALL_DIR/scripts/"

# Copy .env if it exists
if [ -f "$SCRIPT_DIR/.env" ]; then
    cp "$SCRIPT_DIR/.env" "$INSTALL_DIR/"
    print_status "Copied .env file to $INSTALL_DIR"
else
    print_warning ".env file not found in $SCRIPT_DIR. Ensure it's created in $INSTALL_DIR manually if needed."
fi

# Make scripts executable
chmod +x "$INSTALL_DIR/scripts/detect-gpu.sh"
chmod +x "$INSTALL_DIR/scripts/install.sh"
chmod +x "$INSTALL_DIR/scripts/uninstall.sh"
chmod +x "$INSTALL_DIR/scripts/ollama_docker.sh"


print_status "Updating docker-compose.yml with user home directory..."
if [ -z "$SUDO_USER" ]; then
    print_warning "SUDO_USER environment variable not set. Using /root as home directory."
    USER_HOME="/root"
else
    USER_HOME=$(getent passwd "$SUDO_USER" | cut -d: -f6)
    if [ -z "$USER_HOME" ]; then
        print_error "Could not determine home directory for user $SUDO_USER. Exiting."
        exit 1
    fi
    print_status "Using home directory: $USER_HOME"
fi

COMPOSE_FILE="$INSTALL_DIR/docker-compose.yml"
if [ -f "$COMPOSE_FILE" ]; then
    # Use # as sed delimiter to avoid issues with / in paths
    sed -i "s#\${HOME}/.ollama#${USER_HOME}/.ollama#g" "$COMPOSE_FILE"
    print_status "Updated volume paths in $COMPOSE_FILE"
else
    print_warning "docker-compose.yml not found in $INSTALL_DIR. Skipping update."
fi

# Detect if running with GPU
if command -v nvidia-smi &> /dev/null && nvidia-smi &> /dev/null; then
    print_status "NVIDIA GPU detected - service will use GPU profile"
else
    print_warning "No NVIDIA GPU detected - service will use CPU profile"
fi

print_status "Setting up systemd service..."
# Copy the service file from the source directory, not the install directory yet
cp "$SCRIPT_DIR/gov-fetch.service" /etc/systemd/system/

# Reload systemd, enable and start service
print_status "Enabling and starting Gov Fetch service..."
systemctl daemon-reload
systemctl enable gov-fetch
systemctl start gov-fetch

print_status "Installation complete!"
print_status "Service status: $(systemctl is-active gov-fetch)"
print_status "Check logs with: journalctl -u gov-fetch -f"


