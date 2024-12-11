#!/bin/bash

REPO_DIR="/home/pi/test-ai/"

# Verzeichnis der virtuellen Umgebung
VENV_DIR="/home/pi/test-ai/venv"

# Wechsle in das Verzeichnis des Repositories
cd $REPO_DIR

# Hole die neuesten Änderungen
git pull https://andremotz@gitlab.prometheus-it.art/andre/animal_detector.git

# Aktiviere die virtuelle Umgebung
source $VENV_DIR/bin/activate

# Installiere requirements.txt Abhängigkeiten
pip install -r requirements.txt

# Führe das Python-Skript aus
python3 main.py

# Deaktiviere die virtuelle Umgebung (optional, wenn der Prozess endet)
deactivate