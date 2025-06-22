#!/bin/bash

# Hole die neuesten Änderungen
git config --global credential.helper store
git pull https://andremotz@gitlab.prometheus-it.art/andre/animal_detector.git

# Entferne die config.txt aus dem Index
git rm --cached config.txt

# Verzeichnis des Repositories, was dasselbe ist, wie das Verzeichnis dieses Skripts + /ipcam-detector
REPO_DIR=$(pwd)/ipcam-detector

# Verzeichnis der virtuellen Umgebung
# VENV_DIR basierend auf REPO_DIR setzen
VENV_DIR="${REPO_DIR}/venv"

# Wechsle in das Verzeichnis des Repositories
cd $REPO_DIR

# add a check for source if it exists, if not create it
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv $VENV_DIR
fi

# Aktiviere die virtuelle Umgebung
source $VENV_DIR/bin/activate

# Prüfe, ob requirements.txt sich geändert hat seit der letzten Installation
REQUIREMENTS_FILE="${REPO_DIR}/requirements.txt"
INSTALL_MARKER="${VENV_DIR}/.requirements_installed"

if [ ! -f "$INSTALL_MARKER" ] || [ "$REQUIREMENTS_FILE" -nt "$INSTALL_MARKER" ]; then
    echo "Requirements haben sich geändert oder wurden noch nie installiert. Installiere..."
    pip install -r requirements.txt
    touch "$INSTALL_MARKER"
else
    echo "Requirements sind aktuell. Überspringe Installation."
fi

# Führe das Python-Skript aus mit den globalen Variablen RTSP_STREAM_URL und OUTPUT_DIR
python3 main.py $REPO_DIR/results

# Deaktiviere die virtuelle Umgebung (optional, wenn der Prozess endet)
deactivate