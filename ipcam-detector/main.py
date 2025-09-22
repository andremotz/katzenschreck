import cv2
import os
import time
from ultralytics import YOLO
import argparse
import paho.mqtt.client as mqtt
import threading
from results_cleanup import cleanup_results_folder
from typing import Optional, List, Tuple
import json
import mysql.connector
from mysql.connector import Error


class Config:
    """Konfigurationsklasse für das Katzenschreck-System"""
    
    def __init__(self, config_file_path: str):
        self.config_file_path = config_file_path
        self._load_config()
        self._validate_config()
    
    def _load_config(self):
        """Lädt die Konfiguration aus der Datei"""
        config = {}
        with open(self.config_file_path, 'r') as file:
            for line in file:
                if '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
        
        self.rtsp_stream_url = config.get('rtsp_stream_url')
        self.mqtt_broker_url = config.get('mqtt_broker_url')
        self.mqtt_broker_port = int(config.get('mqtt_broker_port', 1883))
        self.mqtt_topic = config.get('mqtt_topic')
        self.mqtt_username = config.get('mqtt_username')
        self.mqtt_password = config.get('mqtt_password')
        self.confidence_threshold = float(config.get('confidence_threshold', 0.5))
        self.usage_threshold = float(config.get('usage_threshold', 0.8))
        
        # Datenbank-Konfiguration
        self.db_host = config.get('db_host', 'localhost')
        self.db_user = config.get('db_user', 'katzenschreck_app')
        self.db_password = config.get('db_password', 'p7eWPjGeIRXtMvCJw--')
        self.db_database = config.get('db_database', 'katzenschreck')
        self.camera_name = config.get('camera_name', 'cam_garten')
        
        ignore_zone_str = config.get('ignore_zone')
        if ignore_zone_str:
            self.ignore_zone = [float(x) for x in ignore_zone_str.split(',')]
        else:
            self.ignore_zone = None
    
    def _validate_config(self):
        """Validiert die Konfiguration"""
        required_fields = [
            ('rtsp_stream_url', self.rtsp_stream_url),
            ('mqtt_broker_url', self.mqtt_broker_url),
            ('mqtt_topic', self.mqtt_topic),
            ('mqtt_username', self.mqtt_username),
            ('mqtt_password', self.mqtt_password)
        ]
        
        for field_name, field_value in required_fields:
            if not field_value:
                raise ValueError(f"{field_name} not found in config.txt")


class MQTTHandler:
    """MQTT-Handler für die Kommunikation mit dem MQTT-Broker"""
    
    def __init__(self, config: Config):
        self.config = config
        self.ping_thread = None
        self._start_ping_thread()
    
    def _start_ping_thread(self):
        """Startet den MQTT-Ping-Thread"""
        self.ping_thread = threading.Thread(target=self._mqtt_ping)
        self.ping_thread.daemon = True
        self.ping_thread.start()
    
    def _mqtt_ping(self):
        """Sendet alle 30 Sekunden einen Ping an den MQTT-Broker"""
        while True:
            time.sleep(30)
            client = mqtt.Client()
            client.username_pw_set(self.config.mqtt_username, self.config.mqtt_password)
            try:
                client.connect(self.config.mqtt_broker_url, self.config.mqtt_broker_port, 60)
                client.loop_start()
                extended_topic = f'{self.config.mqtt_topic}/ping'
                current_timestamp = int(time.time())
                client.publish(extended_topic, json.dumps({"timestamp": current_timestamp}))
                client.loop_stop()
                client.disconnect()
            except Exception as e:
                print(f"MQTT Ping Fehler: {e}")
    
    def publish_detection(self, class_name: str, confidence: float, timestamp: str):
        """Sendet eine Erkennungs-Nachricht an den MQTT-Broker"""
        client = mqtt.Client()
        client.username_pw_set(self.config.mqtt_username, self.config.mqtt_password)
        
        try:
            client.connect(self.config.mqtt_broker_url, self.config.mqtt_broker_port, 60)
            extended_topic = f'{self.config.mqtt_topic}/{class_name}'
            message = json.dumps({
                "time": timestamp,
                "class": class_name,
                "confidence": confidence
            })
            client.publish(extended_topic, message)
            client.disconnect()
        except Exception as e:
            print(f"MQTT Publish Fehler: {e}")


class DatabaseHandler:
    """Datenbank-Handler für MariaDB-Verbindung"""
    
    def __init__(self, config: Config):
        self.config = config
    
    def _get_connection(self):
        """Erstellt eine neue Datenbankverbindung"""
        try:
            connection = mysql.connector.connect(
                host=self.config.db_host,
                user=self.config.db_user,
                password=self.config.db_password,
                database=self.config.db_database
            )
            return connection
        except Error as e:
            print(f"Fehler bei der Datenbankverbindung: {e}")
            return None
    
    def save_frame_to_database(self, frame, accuracy: float = 1.0):
        """Speichert den aktuellen Frame als JPEG in die Datenbank"""
        connection = self._get_connection()
        if not connection:
            return False
        
        try:
            cursor = connection.cursor()
            
            # Frame in JPEG-Format konvertieren (Original-Auflösung beibehalten)
            success, jpeg_buffer = cv2.imencode('.jpg', frame)
            if not success:
                print("Fehler beim Konvertieren des Frames zu JPEG")
                return False
            
            jpeg_data = jpeg_buffer.tobytes()
            
            # Insert-Statement ausführen
            sql = """
            INSERT INTO detections_images (camera_name, accuracy, blob_jpeg)
            VALUES (%s, %s, %s)
            """
            values = (self.config.camera_name, accuracy, jpeg_data)
            
            cursor.execute(sql, values)
            connection.commit()
            
            print(f"Frame erfolgreich in Datenbank gespeichert (Größe: {len(jpeg_data)} Bytes)")
            cursor.close()
            connection.close()
            return True
            
        except Error as e:
            print(f"Fehler beim Speichern in die Datenbank: {e}")
            if connection:
                connection.close()
            return False


class ObjectDetector:
    """YOLO-Objekterkennungsklasse"""
    
    CLASS_NAMES = {0: 'Person', 15: 'Cat'}
    TARGET_CLASS_ID = 15  # Katze
    
    def __init__(self, model_path: str = 'yolo12x.pt'):
        self.model = YOLO(model_path)
    
    def detect_objects(self, frame) -> Tuple[List[Tuple[int, float, List[float]]], object]:
        """Erkennt Objekte im Frame und gibt relevante Erkennungen zurück"""
        results = self.model(frame)
        detections = []
        
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls.item())
                
                # Nur Katzen erkennen (und keine Personen)
                if class_id == self.TARGET_CLASS_ID and class_id != 0:
                    confidence = box.conf.item()
                    bbox = box.xyxy[0].tolist()  # [x1, y1, x2, y2]
                    detections.append((class_id, confidence, bbox))
        
        return detections, results
    
    def is_in_ignore_zone(self, bbox: List[float], frame_shape: Tuple[int, int], ignore_zone: Optional[List[float]]) -> bool:
        """Prüft, ob die Bounding Box in der Ignore-Zone liegt"""
        if not ignore_zone:
            return False
        
        x1, y1, x2, y2 = bbox
        frame_h, frame_w = frame_shape[:2]
        
        # Box-Koordinaten als Prozentwerte
        box_xmin = x1 / frame_w
        box_ymin = y1 / frame_h
        box_xmax = x2 / frame_w
        box_ymax = y2 / frame_h
        
        # Ignore-Zone-Koordinaten
        iz_xmin, iz_ymin, iz_xmax, iz_ymax = ignore_zone
        
        # Prüfe, ob sich die Box mit der Ignore-Zone überschneidet
        return not (box_xmax < iz_xmin or box_xmin > iz_xmax or box_ymax < iz_ymin or box_ymin > iz_ymax)


class StreamProcessor:
    """Hauptklasse für die Verarbeitung des Video-Streams"""
    
    def __init__(self, config: Config, output_dir: str):
        self.config = config
        self.output_dir = output_dir
        self.detector = ObjectDetector()
        self.mqtt_handler = MQTTHandler(config)
        self.db_handler = DatabaseHandler(config)
        
        # Frame-Timing für minutenbasierte Speicherung
        self.last_frame_save_time = 0
        self.frame_save_interval = 60  # 60 Sekunden = 1 Minute
        
        # Erstelle Ausgabeverzeichnis
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def _save_detection(self, annotated_frame, timestamp: str):
        """Speichert das erkannte Frame"""
        cleanup_results_folder(self.output_dir, self.config.usage_threshold)
        output_file = f'{self.output_dir}/frame_{timestamp}.jpg'
        cv2.imwrite(output_file, annotated_frame)
    
    def _resize_frame_to_fullhd(self, frame):
        """Reduziert die Frame-Auflösung von 4K auf Full HD (1920x1080)"""
        height, width = frame.shape[:2]
        
        # Zielauflösung: Full HD (1920x1080)
        target_width = 1920
        target_height = 1080
        
        # Nur resizen wenn der Frame größer als Full HD ist
        if width > target_width or height > target_height:
            resized_frame = cv2.resize(frame, (target_width, target_height), interpolation=cv2.INTER_AREA)
            print(f"Frame von {width}x{height} auf {target_width}x{target_height} reduziert")
            return resized_frame
        else:
            # Frame ist bereits Full HD oder kleiner
            return frame
    
    def _save_frame_to_database_if_needed(self, frame):
        """Speichert den aktuellen Frame in die Datenbank, wenn eine Minute vergangen ist"""
        current_time = time.time()
        
        if current_time - self.last_frame_save_time >= self.frame_save_interval:
            self.last_frame_save_time = current_time
            success = self.db_handler.save_frame_to_database(frame)
            if success:
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                print(f"Frame in Datenbank gespeichert um {timestamp}")
            return success
        
        return False
    
    def _process_detections(self, frame, detections, results):
        """Verarbeitet die Erkennungen"""
        for class_id, confidence, bbox in detections:
            if confidence > self.config.confidence_threshold:
                # Prüfe Ignore-Zone
                if self.detector.is_in_ignore_zone(bbox, frame.shape, self.config.ignore_zone):
                    continue
                
                # Annotiere Frame
                annotated_frame = None
                for result in results:
                    annotated_frame = result.plot()
                    break
                
                if annotated_frame is None:
                    continue
                
                # Zeitstempel generieren
                timestamp = time.strftime('%Y-%m-%d_%H-%M-%S-%f')[:-3]
                
                # Frame speichern
                self._save_detection(annotated_frame, timestamp)
                
                # Informationen ausgeben
                class_name = self.detector.CLASS_NAMES.get(class_id, "Unknown")
                print(f'Detected class ID: {class_id}')
                print(f'Detected class name: {class_name}')
                print(f'Detected class confidence: {confidence}')
                
                # MQTT-Nachricht senden
                self.mqtt_handler.publish_detection(class_name, confidence, timestamp)
    
    def run(self):
        """Hauptschleife für die Stream-Verarbeitung"""
        while True:
            cap = cv2.VideoCapture(self.config.rtsp_stream_url)
            
            if not cap.isOpened():
                print(f"Fehler beim Öffnen des RTSP-Streams: {self.config.rtsp_stream_url}. Versuche erneut in 5 Sekunden...")
                time.sleep(5)
                continue
            
            print("Verbindung zum RTSP-Stream erfolgreich aufgebaut.")
            
            # Verarbeite Frames
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Frame-Auflösung von 4K auf Full HD reduzieren
                frame = self._resize_frame_to_fullhd(frame)
                
                # Speichere Frame jede Minute in die Datenbank
                self._save_frame_to_database_if_needed(frame)
                
                # Objekterkennung
                detections, results = self.detector.detect_objects(frame)
                
                # Verarbeite Erkennungen
                if detections:
                    self._process_detections(frame, detections, results)
                
                # Beende bei 'q'
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    cap.release()
                    return
            
            cap.release()
        
        print(f'Frames mit erkannten Objekten sind im Ordner "{self.output_dir}" gespeichert.')


class KatzenschreckApp:
    """Hauptanwendungsklasse"""
    
    def __init__(self):
        self.args = self._parse_arguments()
        self.config = Config('../config.txt')
        self.processor = StreamProcessor(self.config, self.args.output_dir)
    
    def _parse_arguments(self):
        """Parst die Kommandozeilenargumente"""
        parser = argparse.ArgumentParser(description="RTSP-Stream verarbeiten und erkannte Frames speichern.")
        parser.add_argument("output_dir", type=str, help="Der Ordner, in dem die erkannten Frames gespeichert werden.")
        return parser.parse_args()
    
    def run(self):
        """Startet die Anwendung"""
        self.processor.run()


def main():
    """Hauptfunktion"""
    app = KatzenschreckApp()
    app.run()


if __name__ == "__main__":
    main()