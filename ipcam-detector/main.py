import cv2
import os
import time
from ultralytics import YOLO
import argparse
import paho.mqtt.client as mqtt
import threading
from results_cleanup import cleanup_results_folder

# MQTT connection status
mqtt_connected = False

# MQTT callbacks
def on_connect(client, userdata, flags, rc):
    global mqtt_connected
    if rc == 0:
        print("Connected to MQTT broker successfully")
        mqtt_connected = True
    else:
        print(f"Failed to connect to MQTT broker with code: {rc}")
        mqtt_connected = False

def on_disconnect(client, userdata, rc):
    global mqtt_connected
    print(f"Disconnected from MQTT broker with code: {rc}")
    mqtt_connected = False

def connect_mqtt():
    global mqtt_broker
    try:
        mqtt_broker = mqtt.Client()
        mqtt_broker.username_pw_set(mqtt_username, mqtt_password)
        mqtt_broker.on_connect = on_connect
        mqtt_broker.on_disconnect = on_disconnect
        mqtt_broker.connect(mqtt_broker_url, mqtt_broker_port, 60)
        mqtt_broker.loop_start()
        return True
    except Exception as e:
        print(f"Error connecting to MQTT broker: {e}")
        return False

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
confidence_threshold = float(config.get('confidence_threshold', 0.5))  # Default to 0.5 if not specified
ignore_zone_str = config.get('ignore_zone')
if ignore_zone_str:
    ignore_zone = [float(x) for x in ignore_zone_str.split(',')]
else:
    ignore_zone = None
usage_threshold = float(config.get('usage_threshold', 0.8))  # Default zu 0.8 falls nicht gesetzt

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
connect_mqtt()

# Function to send a ping to the MQTT broker every 30 seconds
def mqtt_ping():
    while True:
        time.sleep(30)
        if not mqtt_connected:
            print("Attempting to reconnect to MQTT broker...")
            connect_mqtt()
        if mqtt_connected:
            try:
                extended_mqtt_topic = f'{mqtt_topic}/ping'
                current_timestamp = int(time.time())
                mqtt_broker.publish(extended_mqtt_topic, f'{{"timestamp": {current_timestamp}}}')
            except Exception as e:
                print(f"Error sending MQTT ping: {e}")
                mqtt_connected = False

# Start the MQTT ping thread
ping_thread = threading.Thread(target=mqtt_ping)
ping_thread.daemon = True
ping_thread.start()

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
        if not ret:
            break

        # Führe die Objekterkennung auf dem aktuellen Frame durch
        results = model(frame)

        for result in results:
            for box in result.boxes:
                # Extract the class ID from the tensor
                class_id = int(box.cls.item())
                
                # Klasse 0 ist 'Person' und Klasse 15 ist 'Katze' (COCO-Datensatzklassennummern)
                if class_id == 0 or class_id == 15:
                    # mache nur weiter, wenn die accuracy über dem konfigurierten Schwellenwert ist
                    if box.conf > confidence_threshold:
                        # Prüfe, ob die Box in der Ignore-Zone liegt
                        if ignore_zone:
                            # Box-Koordinaten (x1, y1, x2, y2) in Pixel
                            x1, y1, x2, y2 = box.xyxy[0].tolist()
                            frame_h, frame_w = frame.shape[:2]
                            # Box-Koordinaten als Prozentwerte
                            box_xmin = x1 / frame_w
                            box_ymin = y1 / frame_h
                            box_xmax = x2 / frame_w
                            box_ymax = y2 / frame_h
                            # Ignore-Zone-Koordinaten
                            iz_xmin, iz_ymin, iz_xmax, iz_ymax = ignore_zone
                            # Prüfe, ob sich die Box mit der Ignore-Zone überschneidet
                            if not (box_xmax < iz_xmin or box_xmin > iz_xmax or box_ymax < iz_ymin or box_ymin > iz_ymax):
                                continue  # Box liegt (ganz oder teilweise) in der Ignore-Zone, also überspringen
                        # Zeichne die erkannten Objekte auf dem Frame
                        annotated_frame = result.plot()

                        # this variable returns the current date and time in the format 'YYYY-MM-DD_HH-MM-SS-MS'
                        current_date_time = time.strftime('%Y-%m-%d_%H-%M-%S-%f')[:-3]

                        # Vor dem Speichern: Speicherplatz prüfen und ggf. alte Bilder löschen
                        cleanup_results_folder(output_dir, usage_threshold)
                        # Speichere das Frame mit den erkannten Objekten
                        output_file = f'{output_dir}/frame_{current_date_time}.jpg'
                        cv2.imwrite(output_file, annotated_frame)

                        # Klasse 0 ist 'Person' und Klasse 15 ist 'Katze' (COCO-Datensatzklassennummern)
                        class_names = {0: 'Person', 15: 'Cat'}

                        # Print the class ID to the terminal
                        detected_class_id = int(box.cls.item())
                        detected_class_name = class_names.get(detected_class_id, "Unknown")
                        detected_class_confidence = box.conf.item()
                        print(f'Detected class ID: {detected_class_id}')
                        print(f'Detected class name: {detected_class_name}')
                        print(f'Detected class confidence: {detected_class_confidence}')

                        # Open MQTT connection and send message
                        if not mqtt_connected:
                            print("Attempting to reconnect to MQTT broker...")
                            connect_mqtt()
                        
                        if mqtt_connected:
                            try:
                                # Extend mqtt_topic with detected_class_name
                                extended_mqtt_topic = f'{mqtt_topic}/{detected_class_name}'

                                # Send MQTT Message
                                mqtt_broker.publish(extended_mqtt_topic, 
                                    f'{{"time": "{current_date_time}", "class": "{detected_class_name}", "confidence": "{detected_class_confidence}"}}')
                            except Exception as e:
                                print(f"Error sending MQTT message: {e}")
                                mqtt_connected = False
                        else:
                            print("Could not send MQTT message - not connected to broker")

        # Zeige den Stream in einem Fenster an
        # cv2.imshow('Live Camera Detection', annotated_frame)

        # Drücke 'q', um den Stream zu beenden
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        # Kamera- und Fenster-Ressourcen freigeben
        cap.release()

print(f'Frames mit erkannten Objekten sind im Ordner "{output_dir}" gespeichert.')
