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

# Lade das YOLO-Modell
model = YOLO('yolo11n.pt')  # 'yolo11n.pt' ist die Nano-Version, du kannst andere Varianten wählen

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
                # Extract the class ID from the tensor
                class_id = int(box.cls.item())
                
                # Klasse 0 ist 'Person' und Klasse 15 ist 'Katze' (COCO-Datensatzklassennummern)
                if class_id == 0 or class_id == 15:
                    # mache nur weiter, wenn die accuracy über 50% ist
                    if box.conf > 0.5:
                        # this variable returns the current date and time in the format 'YYYY-MM-DD_HH-MM-SS-MS'
                        current_date_time = time.strftime('%Y-%m-%d_%H-%M-%S-%f')[:-3]

                        # Speichere das Frame mit den erkannten Objekten
                        output_file = f'{output_dir}/frame_{current_date_time}.jpg'
                        cv2.imwrite(output_file, result.plot())

                        # Klasse 0 ist 'Person' und Klasse 15 ist 'Katze' (COCO-Datensatzklassennummern)
                        class_names = {0: 'Person', 15: 'Cat'}

                        # Print the class ID to the terminal
                        detected_class_id = int(box.cls.item())
                        detected_class_name = class_names.get(detected_class_id, "Unknown")
                        detected_class_confidence = box.conf.item()
                        print(f'Detected class ID: {detected_class_id}')
                        print(f'Detected class name: {detected_class_name}')
                        print(f'Detected class confidence: {detected_class_confidence}')

                        # Open MQTT connection
                        mqtt_broker.connect(mqtt_broker_url, mqtt_broker_port, 60)

                        # Sende eine MQTT Message an den Broker mqtt_broker mit dem Topic mqtt_topic und der entprechend erkannten class_id und current_date_time im json Format
                        mqtt_broker.publish(mqtt_topic, f'{{"time": "{current_date_time}", "class": "{detected_class_name}", "confidence": "{detected_class_confidence}"}}')

                        # Close MQTT connection
                        mqtt_broker.disconnect()

        # Kamera- und Fenster-Ressourcen freigeben
        cap.release()

print(f'Frames mit erkannten Objekten sind im Ordner "{output_dir}" gespeichert.')
