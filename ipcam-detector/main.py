import cv2
import os
import time
from ultralytics import YOLO
import argparse
import paho.mqtt.client as mqtt

# Function to read the configuration from [config.txt](http://_vscodecontentref_/2)
def read_config(file_path):
    config = {}
    with open(file_path, 'r') as file:
        for line in file:
            if '=' in line:
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip()
    return config

# Argumente definieren
parser = argparse.ArgumentParser(description="RTSP-Stream verarbeiten und erkannte Frames speichern.")
parser.add_argument("output_dir", type=str, help="Der Ordner, in dem die erkannten Frames gespeichert werden.")
args = parser.parse_args()

# Konfigurationswerte aus [config.txt](http://_vscodecontentref_/3) lesen
config_file_path = '../config.txt'
config = read_config(config_file_path)
rtsp_stream_url = config.get('rtsp_stream_url')
mqtt_broker_url = config.get('mqtt_broker_url')
mqtt_broker_port = int(config.get('mqtt_broker_port', 1883))  # Default to 1883 if not specified
mqtt_topic = config.get('mqtt_topic')
mqtt_username = config.get('mqtt_username')
mqtt_password = config.get('mqtt_password')

if not rtsp_stream_url:
    raise ValueError("RTSP stream URL not found in config.txt")
if not mqtt_broker_url:
    raise ValueError("MQTT broker URL not found in config.txt")
if not mqtt_topic:
    raise ValueError("MQTT topic not found in config.txt")
if not mqtt_username:
    raise ValueError("MQTT username not found in config.txt")
if not mqtt_password:
    raise ValueError("MQTT password not found in config.txt")

# Zielordner für die Frames aus den Argumenten
output_dir = args.output_dir

# Erstelle einen Ordner, um die Ergebnisse zu speichern, falls er nicht existiert
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# MQTT Broker konfigurieren
mqtt_broker = mqtt.Client()
mqtt_broker.username_pw_set(mqtt_username, mqtt_password)
mqtt_broker.connect(mqtt_broker_url, mqtt_broker_port, 60)

# Lade das YOLO-Modell
model = YOLO('yolo11n.pt')  # 'yolo11n.pt' ist die Nano-Version, du kannst andere Varianten wählen

frame_count = 0

# Verarbeite den Kamera-Stream in Echtzeit
while True:
    cap = cv2.VideoCapture(rtsp_stream_url)

    # Überprüfen, ob der Stream korrekt geöffnet wurde
    if not cap.isOpened():
        print(f"Fehler beim Öffnen des RTSP-Streams: {rtsp_stream_url}. Versuche erneut in 5 Sekunden...")
        time.sleep(5)
        continue  # Versuche erneut

    print("Verbindung zum RTSP-Stream erfolgreich aufgebaut.")

    # Verarbeite Frames, bis der Stream abbricht
    while cap.isOpened():
        ret, frame = cap.read()

        ret, frame = cap.read()
        if not ret:
            break

        # Führe die Objekterkennung auf dem aktuellen Frame durch
        results = model(frame)

        # Standardmäßig kein annotiertes Frame
        annotated_frame = frame.copy()

        # Filtere nur die Erkennung von Menschen (Klasse 0) und Katzen (Klasse 15)
        for result in results:
            for box in result.boxes:
                # Klasse 0 ist 'Person' und Klasse 15 ist 'Katze' (COCO-Datensatzklassennummern)
                if box.cls == 0 or box.cls == 15:
                    # mache nur weiter, wenn die accuracy über 50% ist
                    if box.conf > 0.5:
                        # Zeichne die erkannten Objekte auf dem Frame
                        annotated_frame = result.plot()

                        # this variable returns the current date and time in the format 'YYYY-MM-DD_HH-MM-SS'
                        current_date_time = time.strftime('%Y-%m-%d_%H-%M-%S')

                        # Speichere das Frame mit den erkannten Objekten
                        output_file = f'{output_dir}/frame_{current_date_time}_{frame_count}.jpg'
                        cv2.imwrite(output_file, annotated_frame)
                        frame_count += 1

                        # Klasse 0 ist 'Person' und Klasse 15 ist 'Katze' (COCO-Datensatzklassennummern)
                        class_names = {0: 'Person', 15: 'Cat'}

                        # Sende eine MQTT Message an den Broker mqtt_broker mit dem Topic mqtt_topic und der entprechend erkannten box.cls und current_date_time im json Format
                        mqtt_broker.publish(mqtt_topic, f'{{"cls": "{class_names.get(box.cls, "Unknown")}", "time": "{current_date_time}"}}')

        # Zeige den Stream in einem Fenster an
        # cv2.imshow('Live Camera Detection', annotated_frame)

        # Drücke 'q', um den Stream zu beenden
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        # Kamera- und Fenster-Ressourcen freigeben
        cap.release()
        # cv2.destroyAllWindows()

print(f'Frames mit erkannten Objekten sind im Ordner "{output_dir}" gespeichert.')
