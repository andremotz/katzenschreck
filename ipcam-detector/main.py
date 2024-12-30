import cv2
import os
import time
from ultralytics import YOLO
import argparse
import paho.mqtt.client as mqtt

# Argumente definieren
parser = argparse.ArgumentParser(description="RTSP-Stream verarbeiten und erkannte Frames speichern.")
parser.add_argument("rtsp_stream_url", type=str, help="Die URL des RTSP-Streams.")
parser.add_argument("output_dir", type=str, help="Der Ordner, in dem die erkannten Frames gespeichert werden.")
parser.add_argument("mqtt_broker_url", type=str, help="Der MQTT Broker, der die erkannten Objekte empfängt.")
parser.add_argument("mqtt_topic", type=str, help="Der MQTT Topic, der die erkannten Objekte empfängt.")
args = parser.parse_args()

# RTSP-Stream-URL und Zielordner für die Frames aus den Argumenten
rtsp_stream_url = args.rtsp_stream_url
output_dir = args.output_dir
mqtt_broker_url = args.mqtt_broker_url
mqtt_topic = args.mqtt_topic

# Erstelle einen Ordner, um die Ergebnisse zu speichern, falls er nicht existiert
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# MQTT Broker konfigurieren
mqtt_broker = mqtt.Client()
mqtt_broker.connect(mqtt_broker_url, 1883, 60)

# Lade das YOLO11-Modell
model = YOLO('yolo11n.pt')  # 'yolo11n.pt' ist die Nano-Version, du kannst andere Varianten wählen

# Zugriff auf die MacBook-Kamera (Kamera-ID 0 ist normalerweise die interne Kamera)
# cap = cv2.VideoCapture(0)

frame_count = 0

# Verarbeite den Kamera-Stream in Echtzeit
#while cap.isOpened():
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
