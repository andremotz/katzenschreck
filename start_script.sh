#!/bin/bash

# Konfigurationsdatei einlesen
CONFIG_FILE="config.txt"

if [ -f "$CONFIG_FILE" ]; then
    # Datei einlesen und Variablen exportieren
    source "$CONFIG_FILE"
else
    echo "Config file $CONFIG_FILE not found!"
    exit 1
fi

# Verzeichnis der virtuellen Umgebung
# VENV_DIR basierend auf REPO_DIR setzen
VENV_DIR="${REPO_DIR}/venv"

# Wechsle in das Verzeichnis des Repositories
cd $REPO_DIR

# Hole die neuesten Änderungen
git pull https://andremotz@gitlab.prometheus-it.art/andre/animal_detector.git

# Entferne die config.txt aus dem Index
git rm --cached config.txt

# add a check for source if it exists, if not create it
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv $VENV_DIR
fi

# Aktiviere die virtuelle Umgebung
source $VENV_DIR/bin/activate

# Installiere requirements.txt Abhängigkeiten
pip install -r ipcam-detector/requirements.txt

# Führe das Python-Skript aus mit den globalen Variablen RTSP_STREAM_URL und OUTPUT_DIR
python3 ipcam-detector/main.py $RTSP_STREAM_URL $OUTPUT_DIR

# Deaktiviere die virtuelle Umgebung (optional, wenn der Prozess endet)
deactivate