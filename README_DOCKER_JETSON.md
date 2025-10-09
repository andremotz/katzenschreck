# Katzenschreck on Jetson with Docker

This guide explains how to run Katzenschreck on an NVIDIA Jetson using the ultralytics Docker container.

## Prerequisites

1. NVIDIA Jetson with JetPack installed
2. Docker and nvidia-container-runtime installed
3. Git installed

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/andremotz/katzenschreck.git
cd katzenschreck
```

### 2. Create Config File

```bash
cp config.txt.example config.txt
nano config.txt
```

Make sure to set `hardware_type=jetson` in `config.txt`:

```
# Hardware Type Override (optional)
hardware_type=jetson
```

### 3. Build Docker Image

```bash
docker build -f Dockerfile.jetson -t katzenschreck:jetson .
```

## Usage

### Option 1: With Docker Compose (recommended)

```bash
docker-compose -f docker-compose.jetson.yml up -d
```

View logs:
```bash
docker-compose -f docker-compose.jetson.yml logs -f
```

Stop:
```bash
docker-compose -f docker-compose.jetson.yml down
```

### Option 2: With Docker Run

```bash
docker run -d \
  --name katzenschreck \
  --runtime nvidia \
  --network host \
  -v $(pwd)/config.txt:/app/config.txt:ro \
  -v $(pwd)/results:/app/results \
  -e NVIDIA_VISIBLE_DEVICES=all \
  -e NVIDIA_DRIVER_CAPABILITIES=all \
  --restart unless-stopped \
  katzenschreck:jetson
```

View logs:
```bash
docker logs -f katzenschreck
```

Stop:
```bash
docker stop katzenschreck
docker rm katzenschreck
```

## Important Notes

### Hardware Detection

Since automatic hardware detection doesn't work inside Docker containers, you **must** set the following line in `config.txt`:

```
hardware_type=jetson
```

This ensures that the optimal YOLO11x model for Jetson is used.

### GPU Access

The container requires the NVIDIA Container Runtime for GPU access. Test the installation with:

```bash
docker run --rm --runtime nvidia ultralytics/ultralytics:latest-jetson nvidia-smi
```

### Network

The container uses `network_mode: host` for direct access to RTSP streams in the local network.

### Persistent Data

- **config.txt**: Mounted as read-only
- **results/**: Directory for detected frames is mounted

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs katzenschreck

# Check GPU access
docker run --rm --runtime nvidia katzenschreck:jetson nvidia-smi
```

### Error "No module named 'mysql'"

The Dockerfile installs `mysql-connector-python` automatically. If the error occurs:

```bash
# Rebuild the image
docker-compose -f docker-compose.jetson.yml build --no-cache
```

### RTSP Stream Not Reachable

Make sure `network_mode: host` is set in docker-compose.yml.

## Updates

```bash
# Update code
git pull

# Rebuild image
docker-compose -f docker-compose.jetson.yml build

# Restart container
docker-compose -f docker-compose.jetson.yml up -d
```

## Auto-Start on System Boot

### With Docker Compose

```bash
# Enable Docker service
sudo systemctl enable docker

# Restart policy is already set in docker-compose.yml (unless-stopped)
```

### Systemd Service (Alternative)

Create `/etc/systemd/system/katzenschreck.service`:

```ini
[Unit]
Description=Katzenschreck Cat Detection System
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/youruser/katzenschreck
ExecStart=/usr/bin/docker-compose -f docker-compose.jetson.yml up -d
ExecStop=/usr/bin/docker-compose -f docker-compose.jetson.yml down
User=youruser

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl daemon-reload
sudo systemctl enable katzenschreck.service
sudo systemctl start katzenschreck.service
```

