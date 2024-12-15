#!/bin/bash

# Hole die neuesten Änderungen
git pull https://andremotz@gitlab.prometheus-it.art/andre/animal_detector.git

# Entferne die config.txt aus dem Index
git rm --cached config.txt

# Konfigurationsdatei einlesen
CONFIG_FILE="config.txt"

if [ -f "$CONFIG_FILE" ]; then
    # Datei einlesen und Variablen exportieren
    source "$CONFIG_FILE"
else
    echo "Config file $CONFIG_FILE not found!"
    exit 1
fi

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

# Installiere requirements.txt Abhängigkeiten
pip install -r ipcam-detector/requirements.txt

# Führe das Python-Skript aus mit den globalen Variablen RTSP_STREAM_URL und OUTPUT_DIR
python3 ipcam-detector/main.py $RTSP_STREAM_URL $REPO_DIR/results

# Deaktiviere die virtuelle Umgebung (optional, wenn der Prozess endet)
deactivate