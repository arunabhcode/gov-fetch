# gov_fetch
App to get data from govt websites like USCIS and export control classifications

# Gov Fetch Systemd Service

## Installation

1. Copy the systemd service file to the system directory:

```bash
sudo cp gov-fetch.service /etc/systemd/system/
```

2. Copy the GPU detection script:

```bash
chmod +x detect-gpu.sh
sudo cp detect-gpu.sh /usr/local/bin/
```

3. (Optional) Create a configuration file to specify your Gov Fetch installation directory:

```bash
sudo mkdir -p /etc/default
echo "GOVFETCH_DIR=/path/to/your/gov_fetch" | sudo tee /etc/default/gov-fetch
```

If you skip this step, the service will default to `~/gov_fetch`.

4. Reload the systemd daemon:

```bash
sudo systemctl daemon-reload
```

5. Enable the service to start on boot:

```bash
sudo systemctl enable gov-fetch
```

6. Start the service:

```bash
sudo systemctl start gov-fetch
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

## Monitoring

Check service status:

```bash
sudo systemctl status gov-fetch
```

View logs:

```bash
sudo journalctl -u gov-fetch -f
```

## Dynamic Configuration

The service file uses the following systemd features to be more dynamic:

- `%u` and `%g`: Uses the user and group of the person who started the service
- `%h`: Uses the home directory of the user
- `EnvironmentFile`: Reads configuration from `/etc/default/gov-fetch` if it exists
- Environment variables for locations and profiles
- Automatic GPU detection for selecting the appropriate profile
