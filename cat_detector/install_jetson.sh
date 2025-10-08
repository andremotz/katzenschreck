#!/bin/bash
# Installation script for NVIDIA Jetson Xavier NX

echo "Installing dependencies for Jetson Xavier NX..."

# Update system packages
sudo apt update
sudo apt install -y python3-pip python3-dev python3-venv

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install PyTorch with CUDA support for Jetson
echo "Installing PyTorch with CUDA support..."
pip3 install torch==1.13.1 torchvision==0.14.1 --index-url https://download.pytorch.org/whl/cu117

# Install other requirements
echo "Installing other dependencies..."
pip install -r requirements_jetson.txt

# Download YOLOv8x model
echo "Downloading YOLOv8x model..."
python3 -c "from ultralytics import YOLO; YOLO('yolov8x.pt')"

echo "Installation completed!"
echo "To activate the environment, run: source venv/bin/activate"
