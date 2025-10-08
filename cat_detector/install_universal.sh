#!/bin/bash
# Universal installation script for both Raspberry Pi and Jetson devices

echo "🚀 Installing Katzenschreck - Universal Setup"
echo "=============================================="

# Detect platform
if [ -f /proc/device-tree/model ]; then
    MODEL=$(cat /proc/device-tree/model)
    echo "📱 Detected device: $MODEL"
    
    if [[ $MODEL == *"Jetson"* ]] || [[ $MODEL == *"Xavier"* ]]; then
        PLATFORM="jetson"
        echo "🔧 Platform: NVIDIA Jetson"
    elif [[ $MODEL == *"Raspberry Pi"* ]]; then
        PLATFORM="raspberry"
        echo "🔧 Platform: Raspberry Pi"
    else
        PLATFORM="generic"
        echo "🔧 Platform: Generic Linux"
    fi
else
    PLATFORM="generic"
    echo "🔧 Platform: Generic Linux"
fi

# Update system packages
echo "📦 Updating system packages..."
sudo apt update
sudo apt install -y python3-pip python3-dev python3-venv git

# Create virtual environment
echo "🐍 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install PyTorch based on platform
echo "🔥 Installing PyTorch for $PLATFORM..."
if [ "$PLATFORM" = "jetson" ]; then
    echo "   Installing PyTorch with CUDA support for Jetson..."
    pip install torch==1.13.1 torchvision==0.14.1 --index-url https://download.pytorch.org/whl/cu117
elif [ "$PLATFORM" = "raspberry" ]; then
    echo "   Installing PyTorch CPU-only for Raspberry Pi..."
    pip install torch==1.13.1 torchvision==0.14.1 --index-url https://download.pytorch.org/whl/cpu
else
    echo "   Installing PyTorch (auto-detect CUDA)..."
    pip install torch==1.13.1 torchvision==0.14.1
fi

# Install other requirements
echo "📚 Installing other dependencies..."
pip install -r requirements_universal.txt

# Test hardware detection
echo "🔍 Testing hardware detection..."
python3 -c "
from hardware_detector import HardwareDetector
detector = HardwareDetector()
detector.print_hardware_info()
"

# Download recommended model
echo "📥 Downloading recommended YOLO model..."
python3 -c "
from hardware_detector import HardwareDetector
from ultralytics import YOLO
detector = HardwareDetector()
model_name, _ = detector.get_optimal_model()
print(f'Downloading {model_name}...')
YOLO(model_name)
print('Model downloaded successfully!')
"

echo ""
echo "✅ Installation completed successfully!"
echo "=============================================="
echo "To activate the environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "To start the application, run:"
echo "  python3 main.py"
echo ""
echo "The system will automatically detect your hardware"
echo "and use the optimal YOLO model for your device."
