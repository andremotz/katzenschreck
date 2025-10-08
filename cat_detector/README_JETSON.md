# Katzenschreck - Jetson Xavier NX Setup

This setup is optimized for the NVIDIA Jetson Xavier NX Developer Kit with Python 3.8.10.

## Hardware Requirements

- NVIDIA Jetson Xavier NX Developer Kit
- Minimum 8GB RAM (recommended: 16GB)
- MicroSD card with at least 32GB storage
- Camera (USB or CSI)

## Installation

### 1. Prepare System

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install additional packages
sudo apt install -y python3-pip python3-dev python3-venv git
```

### 2. Install Project

```bash
# Clone repository
git clone <repository-url>
cd katzenschreck

# Switch branch
git checkout feature_yolov8xjetson

# Run installation
cd cat_detector
chmod +x install_jetson.sh
./install_jetson.sh
```

### 3. Activate Virtual Environment

```bash
source venv/bin/activate
```

## YOLOv8x Model

The script uses YOLOv8x by default, which:
- Provides highest accuracy
- Requires more computational power
- Is well-suited for Jetson Xavier NX

### Model Download

The YOLOv8x model is automatically downloaded on first startup (~130MB).

## Performance Optimizations for Jetson

### 1. Enable GPU Mode

```bash
# Jetson clocks for maximum performance
sudo jetson_clocks
```

### 2. Set Power Mode

```bash
# For maximum performance (higher power consumption)
sudo nvpmodel -m 0
sudo jetson_clocks
```

### 3. Memory Management

```bash
# Increase swap memory (if needed)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## Configuration

Configuration is done via the `config.txt` file. Important settings for Jetson:

```ini
# YOLO model
model_path=yolov8x.pt

# Performance settings
confidence_threshold=0.5
nms_threshold=0.4

# Camera settings
camera_width=1280
camera_height=720
fps=15
```

## Troubleshooting

### CUDA Errors
If CUDA errors occur:
```bash
# Check CUDA version
nvcc --version

# Test PyTorch CUDA support
python3 -c "import torch; print(torch.cuda.is_available())"
```

### Memory Issues
For memory problems:
- Use smaller resolution
- Use YOLOv8n or YOLOv8s instead of YOLOv8x
- Increase swap memory

### Performance Issues
- Run `jetson_clocks`
- Set power mode to maximum
- Close other applications

## Monitoring

```bash
# Monitor GPU usage
tegrastats

# Check memory usage
free -h

# CPU temperature
cat /sys/class/thermal/thermal_zone*/temp
```
