# Katzenschreck - Jetson Xavier NX Setup

Dieses Setup ist optimiert für das NVIDIA Jetson Xavier NX Developer Kit mit Python 3.8.10.

## Hardware-Anforderungen

- NVIDIA Jetson Xavier NX Developer Kit
- Mindestens 8GB RAM (empfohlen: 16GB)
- MicroSD-Karte mit mindestens 32GB Speicher
- Kamera (USB oder CSI)

## Installation

### 1. System vorbereiten

```bash
# System aktualisieren
sudo apt update && sudo apt upgrade -y

# Zusätzliche Pakete installieren
sudo apt install -y python3-pip python3-dev python3-venv git
```

### 2. Projekt installieren

```bash
# Repository klonen
git clone <repository-url>
cd katzenschreck

# Branch wechseln
git checkout feature_yolov8xjetson

# Installation ausführen
cd cat_detector
chmod +x install_jetson.sh
./install_jetson.sh
```

### 3. Virtual Environment aktivieren

```bash
source venv/bin/activate
```

## YOLOv8x Modell

Das Script verwendet standardmäßig YOLOv8x, welches:
- Höchste Genauigkeit bietet
- Mehr Rechenleistung benötigt
- Gut für den Jetson Xavier NX geeignet ist

### Modell-Download

Das YOLOv8x-Modell wird automatisch beim ersten Start heruntergeladen (~130MB).

## Performance-Optimierungen für Jetson

### 1. GPU-Modus aktivieren

```bash
# Jetson-Clocks für maximale Performance
sudo jetson_clocks
```

### 2. Power-Modus setzen

```bash
# Für maximale Performance (mehr Stromverbrauch)
sudo nvpmodel -m 0
sudo jetson_clocks
```

### 3. Memory-Management

```bash
# Swap-Speicher erhöhen (falls nötig)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## Konfiguration

Die Konfiguration erfolgt über die `config.txt` Datei. Wichtige Einstellungen für den Jetson:

```ini
# YOLO-Modell
model_path=yolov8x.pt

# Performance-Einstellungen
confidence_threshold=0.5
nms_threshold=0.4

# Kamera-Einstellungen
camera_width=1280
camera_height=720
fps=15
```

## Troubleshooting

### CUDA-Fehler
Falls CUDA-Fehler auftreten:
```bash
# CUDA-Version prüfen
nvcc --version

# PyTorch CUDA-Support testen
python3 -c "import torch; print(torch.cuda.is_available())"
```

### Speicher-Probleme
Bei Speicher-Problemen:
- Kleinere Auflösung verwenden
- YOLOv8n oder YOLOv8s statt YOLOv8x
- Swap-Speicher erhöhen

### Performance-Probleme
- `jetson_clocks` ausführen
- Power-Modus auf Maximum setzen
- Andere Anwendungen schließen

## Monitoring

```bash
# GPU-Nutzung überwachen
tegrastats

# Speicher-Nutzung prüfen
free -h

# CPU-Temperatur
cat /sys/class/thermal/thermal_zone*/temp
```
