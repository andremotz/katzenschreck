# Katzenschreck - IP-Kamera Objekterkennung

Ein System zur automatischen Erkennung von Katzen in IP-Kamera-Streams mit YOLO und Speicherung in MariaDB.

## Features

- **Objekterkennung**: Automatische Erkennung von Katzen mit YOLO
- **MQTT-Integration**: Senden von Benachrichtigungen bei Erkennungen
- **Datenbank-Speicherung**: Automatische Speicherung von Frames jede Minute in MariaDB
- **RTSP-Stream Support**: Unterstützung für IP-Kameras mit RTSP-Protokoll
- **Ignore-Zonen**: Konfigurierbare Bereiche, die ignoriert werden

## Installation

1. Abhängigkeiten installieren:
```bash
cd ipcam-detector
pip install -r requirements.txt
```

2. Datenbank einrichten:
```bash
mysql -u root -p < ../database_setup.sql
```

3. Konfiguration erstellen:
```bash
cp config.txt.example config.txt
# Konfigurationsdatei anpassen
```

## Verwendung

```bash
python ipcam-detector/main.py <output_folder>
```

Die Konfiguration erfolgt über die `config.txt` Datei im Hauptverzeichnis.

## Konfiguration

Die `config.txt` sollte folgende Parameter enthalten:

- **RTSP-Stream**: `rtsp_stream_url`
- **MQTT**: `mqtt_broker_url`, `mqtt_topic`, etc.
- **Datenbank**: `db_host`, `db_user`, `db_password`, `db_database`
- **Objekterkennung**: `confidence_threshold`, `ignore_zone`

## Datenbank-Schema

Das System speichert jede Minute automatisch einen Frame in der `detections_images` Tabelle:
- `camera_name`: Name der Kamera
- `accuracy`: Genauigkeitswert (Standard: 1.0)
- `blob_jpeg`: JPEG-Bilddaten als BLOB
- `created_at`: Zeitstempel der Speicherung