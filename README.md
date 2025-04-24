# Gov Fetch

App to get data from government websites like USCIS and export control classifications

## Installation

To install gov fetch you first need to create a .env file and fill out each of the entries:

```bash
# Clone the repository (if you haven't already)
git clone https://github.com/arunabhcode/gov-fetch.git
cd gov-fetch

# Copy template .env.example file and fill it out
cp .env.example .env

# Run the installation script as root
sudo ./install.sh
```

The installation script will:

1. Build the Docker image
2. Copy files to /opt/gov-fetch
3. Set up the systemd service
4. Automatically detect if you have a GPU and use the appropriate profile
5. Enable and start the service

## Useful Commands

Once installed, you can use these commands to manage Gov Fetch:

```bash
# Reload the systemd daemon (after making changes to service file)
sudo systemctl daemon-reload

# Check service status
sudo systemctl status gov-fetch

# View logs
sudo journalctl -u gov-fetch -f

# Start the service
sudo systemctl start gov-fetch

# Stop the service
sudo systemctl stop gov-fetch

# Restart the service
sudo systemctl restart gov-fetch

# Enable the service to start on boot
sudo systemctl enable gov-fetch

# Disable the service from starting on boot
sudo systemctl disable gov-fetch
```

## Automatic GPU Detection

The service automatically detects whether an NVIDIA GPU is available and selects the appropriate profile:

- If a GPU is detected (`nvidia-smi` is available and working), the GPU profile is used
- If no GPU is detected, the CPU profile is used

No manual configuration is needed for GPU selection. The system will adapt automatically.

## Manual Profile Override

If you want to override the automatic detection:

1. Create a systemd override:

```bash
sudo systemctl edit gov-fetch
```

2. Add the following content to force a specific profile:

```
[Service]
Environment="COMPOSE_PROFILES=cpu"  # or "COMPOSE_PROFILES=gpu"
ExecStartPre=
ExecStart=/usr/bin/docker compose -f ${GOVFETCH_DIR}/docker-compose.yml --profile ${COMPOSE_PROFILES} up
```

3. Restart the service:

```bash
sudo systemctl restart gov-fetch
```

## Uninstallation

To completely remove Gov Fetch from your system:

```bash
# Run the uninstallation script as root
sudo ./uninstall.sh
```

The uninstallation script will:

1. Stop and disable the service
2. Remove the systemd service files
3. Clean up Docker resources
4. Remove the installation directory
