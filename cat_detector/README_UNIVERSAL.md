# Katzenschreck - Universal Setup

This setup automatically detects your hardware platform and uses the optimal YOLO model and configuration.

## Supported Platforms

- **Raspberry Pi 4** (4GB+ RAM) → YOLO12x
- **NVIDIA Jetson Xavier NX** → YOLOv8x  
- **Other Linux devices** → Auto-detected optimal model

## Quick Start

### 1. Clone and Install

```bash
# Clone repository
git clone <repository-url>
cd katzenschreck/cat_detector

# Run universal installation
chmod +x install_universal.sh
./install_universal.sh
```

### 2. Activate Environment

```bash
source venv/bin/activate
```

### 3. Run Application

```bash
python3 main.py
```

The system will automatically:
- Detect your hardware platform
- Select the optimal YOLO model
- Configure performance settings
- Download the required model

## Hardware Detection

The system automatically detects:

| Platform | Detected Model | Requirements | Performance |
|----------|----------------|--------------|-------------|
| Jetson Xavier NX | YOLOv8x | requirements_jetson.txt | High accuracy |
| Jetson (8GB+) | YOLOv8x | requirements_jetson.txt | High accuracy |
| Jetson (4GB+) | YOLOv8l | requirements_jetson.txt | Balanced |
| Jetson (<4GB) | YOLOv8m | requirements_jetson.txt | Fast |
| Raspberry Pi 4 (8GB+) | YOLO12x | requirements.txt | High accuracy |
| Raspberry Pi 4 (4GB+) | YOLO12l | requirements.txt | Balanced |
| Raspberry Pi 4 (<4GB) | YOLO12m | requirements.txt | Fast |
| Other Linux | YOLOv8x/l/m | requirements.txt | Auto-detected |

## Manual Configuration

If you want to override the automatic detection:

```python
from object_detector import ObjectDetector

# Use specific model
detector = ObjectDetector('yolov8x.pt')  # Force YOLOv8x
detector = ObjectDetector('yolo12x.pt')  # Force YOLO12x
detector = ObjectDetector()              # Auto-detect (default)
```

## Platform-Specific Optimizations

### Jetson Devices

```bash
# Enable maximum performance
sudo jetson_clocks
sudo nvpmodel -m 0

# Monitor performance
tegrastats
```

### Raspberry Pi

```bash
# Enable GPU memory split (if needed)
sudo raspi-config
# Advanced Options → Memory Split → 128

# Monitor performance
htop
```

## Troubleshooting

### Hardware Detection Issues

```bash
# Test hardware detection
python3 -c "from hardware_detector import HardwareDetector; HardwareDetector().print_hardware_info()"
```

### Model Download Issues

```bash
# Manually download model
python3 -c "from ultralytics import YOLO; YOLO('yolov8x.pt')"
```

### Performance Issues

- **Too slow**: Use smaller model (yolov8m, yolo12m)
- **Too much memory**: Reduce camera resolution
- **CUDA errors**: Check PyTorch installation

## File Structure

```
cat_detector/
├── hardware_detector.py      # Hardware detection logic
├── object_detector.py        # YOLO detection with auto-detection
├── requirements_universal.txt # Universal requirements
├── requirements_jetson.txt   # Jetson-specific requirements
├── requirements.txt          # Raspberry Pi requirements
├── install_universal.sh      # Universal installation script
├── install_jetson.sh         # Jetson-specific installation
└── README_UNIVERSAL.md       # This file
```

## Benefits

✅ **One codebase** for all platforms  
✅ **Automatic optimization** based on hardware  
✅ **Easy deployment** with single installation script  
✅ **Future-proof** - supports new hardware automatically  
✅ **Backward compatible** - existing configurations still work  

## Migration from Platform-Specific Setup

If you're migrating from a platform-specific setup:

1. **Backup your config**: `cp config.txt config.txt.backup`
2. **Run universal installer**: `./install_universal.sh`
3. **Test detection**: The system will show detected hardware
4. **Verify performance**: Check if the auto-selected model works well
5. **Fine-tune if needed**: Override model selection if necessary
