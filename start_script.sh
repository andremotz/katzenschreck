#!/bin/bash

# Get the latest changes
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

# add a check for source if it exists, if not create it
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv $VENV_DIR
fi

# Activate virtual environment
source $VENV_DIR/bin/activate

# Check if requirements.txt has changed since last installation
REQUIREMENTS_FILE="${REPO_DIR}/requirements.txt"
INSTALL_MARKER="${VENV_DIR}/.requirements_installed"

if [ ! -f "$INSTALL_MARKER" ] || [ "$REQUIREMENTS_FILE" -nt "$INSTALL_MARKER" ]; then
    echo "Requirements have changed or were never installed. Installing..."
    pip install -r requirements.txt
    touch "$INSTALL_MARKER"
else
    echo "Requirements are up to date. Skipping installation."
fi

# Run the Python script with global variables RTSP_STREAM_URL and OUTPUT_DIR
python3 main.py $REPO_DIR/results

# Deactivate virtual environment (optional, when process ends)
deactivate