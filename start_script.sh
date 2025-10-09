#!/bin/bash

# Katzenschreck Universal Start Script
# Automatically detects hardware and uses optimal configuration

echo "🐱 Starting Katzenschreck - Universal Detection System"
echo "======================================================"

# Get the latest changes
echo "📥 Updating repository..."
git config --global credential.helper store
git pull https://github.com/andremotz/katzenschreck.git

# Remove config.txt from index
git rm --cached config.txt

# Repository directory, which is the same as this script's directory + /cat_detector
REPO_DIR=$(pwd)/cat_detector

# Virtual environment directory
# Set VENV_DIR based on REPO_DIR
VENV_DIR="${REPO_DIR}/venv"

# Change to repository directory
cd $REPO_DIR

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "🐍 Creating virtual environment..."
    python3 -m venv $VENV_DIR
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source $VENV_DIR/bin/activate

# Detect hardware and determine optimal requirements file
echo "🔍 Detecting hardware platform..."
python3 -c "
from hardware_detector import HardwareDetector
from config import Config

# Load config to check for hardware_type override
try:
    config = Config('../config.txt')
    hardware_type = config.hardware_type
    if hardware_type:
        print(f'Using hardware_type from config: {hardware_type}')
except:
    hardware_type = None
    print('No hardware_type override found in config')

detector = HardwareDetector(forced_type=hardware_type)
detector.print_hardware_info()
model_name, requirements_file = detector.get_optimal_model()
print(f'Using requirements: {requirements_file}')
print(f'Optimal model: {model_name}')
" > /tmp/hardware_info.txt

# Read hardware detection results
REQUIREMENTS_FILE=$(grep "Using requirements:" /tmp/hardware_info.txt | cut -d' ' -f3)
MODEL_NAME=$(grep "Optimal model:" /tmp/hardware_info.txt | cut -d' ' -f3)

echo "📋 Detected requirements file: $REQUIREMENTS_FILE"
echo "🤖 Optimal model: $MODEL_NAME"

# Check if requirements have changed since last installation
INSTALL_MARKER="${VENV_DIR}/.requirements_installed_${REQUIREMENTS_FILE}"

if [ ! -f "$INSTALL_MARKER" ] || [ "$REQUIREMENTS_FILE" -nt "$INSTALL_MARKER" ]; then
    echo "📦 Installing/updating requirements from $REQUIREMENTS_FILE..."
    
    # Install PyTorch based on platform
    if [[ $REQUIREMENTS_FILE == *"jetson"* ]]; then
        echo "🔥 Installing PyTorch with CUDA support for Jetson..."
        pip install torch==1.13.1 torchvision==0.14.1 --index-url https://download.pytorch.org/whl/cu117
    elif [[ $REQUIREMENTS_FILE == *"universal"* ]]; then
        echo "🔥 Installing PyTorch (auto-detect)..."
        pip install torch==1.13.1 torchvision==0.14.1
    else
        echo "🔥 Installing PyTorch CPU-only for Raspberry Pi..."
        pip install torch==1.13.1 torchvision==0.14.1 --index-url https://download.pytorch.org/whl/cpu
    fi
    
    # Install other requirements
    pip install -r "$REQUIREMENTS_FILE"
    touch "$INSTALL_MARKER"
    echo "✅ Requirements installed successfully!"
else
    echo "✅ Requirements are up to date. Skipping installation."
fi

# Download optimal model if not exists
echo "📥 Checking for optimal model: $MODEL_NAME"
python3 -c "
from ultralytics import YOLO
import os
model_path = '$MODEL_NAME'
if not os.path.exists(model_path):
    print(f'Downloading {model_path}...')
    YOLO(model_path)
    print('Model downloaded successfully!')
else:
    print('Model already exists.')
"

# Run the Python script with global variables RTSP_STREAM_URL and OUTPUT_DIR
echo "🚀 Starting Katzenschreck detection system..."
echo "======================================================"

# Change to parent directory to run as module
cd ..
python3 -m cat_detector.main $REPO_DIR/results

# Deactivate virtual environment (optional, when process ends)
deactivate