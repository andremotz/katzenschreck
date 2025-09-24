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
    """Configuration class for the cat deterrent system"""
    
    def __init__(self, config_file_path: str):
        self.config_file_path = config_file_path
        self._load_config()
        self._validate_config()
    
    def _load_config(self):
        """Loads configuration from file"""
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
        
        # Database configuration
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
        """Validates the configuration"""
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
    """MQTT handler for communication with MQTT broker"""
    
    def __init__(self, config: Config):
        self.config = config
        self.ping_thread = None
        self._start_ping_thread()
    
    def _start_ping_thread(self):
        """Starts the MQTT ping thread"""
        self.ping_thread = threading.Thread(target=self._mqtt_ping)
        self.ping_thread.daemon = True
        self.ping_thread.start()
    
    def _mqtt_ping(self):
        """Sends a ping to the MQTT broker every 30 seconds"""
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
                print(f"MQTT Ping Error: {e}")
    
    def publish_detection(self, class_name: str, confidence: float, timestamp: str):
        """Sends a detection message to the MQTT broker"""
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
            print(f"MQTT Publish Error: {e}")


class DatabaseHandler:
    """Database handler for MariaDB connection"""
    
    def __init__(self, config: Config):
        self.config = config
    
    def _get_connection(self):
        """Creates a new database connection"""
        try:
            connection = mysql.connector.connect(
                host=self.config.db_host,
                user=self.config.db_user,
                password=self.config.db_password,
                database=self.config.db_database
            )
            return connection
        except Error as e:
            print(f"Database connection error: {e}")
            return None
    
    def save_frame_to_database(self, frame, accuracy: float = 0.0):
        """Saves the current frame as JPEG and thumbnail to the database"""
        connection = self._get_connection()
        if not connection:
            return False
        
        try:
            cursor = connection.cursor()
            
            # Convert frame to JPEG format (keeping original resolution)
            success, jpeg_buffer = cv2.imencode('.jpg', frame)
            if not success:
                print("Error converting frame to JPEG")
                return False
            
            jpeg_data = jpeg_buffer.tobytes()
            
            # Create thumbnail with 300 pixel width
            thumbnail_data = self._create_thumbnail(frame, 300)
            if not thumbnail_data:
                print("Error creating thumbnail")
                return False
            
            # Execute insert statement
            sql = """
            INSERT INTO detections_images (camera_name, accuracy, blob_jpeg, thumbnail_jpeg)
            VALUES (%s, %s, %s, %s)
            """
            values = (self.config.camera_name, accuracy, jpeg_data, thumbnail_data)
            
            cursor.execute(sql, values)
            connection.commit()
            
            print(f"Frame successfully saved to database (Original size: {len(jpeg_data)} bytes, Thumbnail: {len(thumbnail_data)} bytes)")
            cursor.close()
            connection.close()
            return True
            
        except Error as e:
            print(f"Error saving to database: {e}")
            if connection:
                connection.close()
            return False
    
    def _create_thumbnail(self, frame, target_width: int):
        """Creates a thumbnail with the specified width while maintaining aspect ratio"""
        try:
            height, width = frame.shape[:2]
            
            # Calculate new height based on aspect ratio
            aspect_ratio = height / width
            target_height = int(target_width * aspect_ratio)
            
            # Scale frame to thumbnail size
            thumbnail = cv2.resize(frame, (target_width, target_height), interpolation=cv2.INTER_AREA)
            
            # Convert thumbnail to JPEG format
            success, thumbnail_buffer = cv2.imencode('.jpg', thumbnail, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if not success:
                return None
            
            return thumbnail_buffer.tobytes()
            
        except Exception as e:
            print(f"Error creating thumbnail: {e}")
            return None


class ObjectDetector:
    """YOLO object detection class"""
    
    CLASS_NAMES = {0: 'Person', 15: 'Cat'}
    TARGET_CLASS_ID = 15  # Cat
    
    def __init__(self, model_path: str = 'yolo12l.pt'):
        self.model = YOLO(model_path)
    
    def detect_objects(self, frame) -> Tuple[List[Tuple[int, float, List[float]]], object]:
        """Detects objects in frame and returns relevant detections"""
        results = self.model(frame)
        detections = []
        
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls.item())
                
                # Only detect cats (not persons)
                if class_id == self.TARGET_CLASS_ID and class_id != 0:
                    confidence = box.conf.item()
                    bbox = box.xyxy[0].tolist()  # [x1, y1, x2, y2]
                    detections.append((class_id, confidence, bbox))
        
        return detections, results
    
    def is_in_ignore_zone(self, bbox: List[float], frame_shape: Tuple[int, int], ignore_zone: Optional[List[float]]) -> bool:
        """Checks if the bounding box is in the ignore zone"""
        if not ignore_zone:
            return False
        
        x1, y1, x2, y2 = bbox
        frame_h, frame_w = frame_shape[:2]
        
        # Box coordinates as percentage values
        box_xmin = x1 / frame_w
        box_ymin = y1 / frame_h
        box_xmax = x2 / frame_w
        box_ymax = y2 / frame_h
        
        # Ignore zone coordinates
        iz_xmin, iz_ymin, iz_xmax, iz_ymax = ignore_zone
        
        # Check if box overlaps with ignore zone
        return not (box_xmax < iz_xmin or box_xmin > iz_xmax or box_ymax < iz_ymin or box_ymin > iz_ymax)


class StreamProcessor:
    """Main class for video stream processing"""
    
    def __init__(self, config: Config, output_dir: str):
        self.config = config
        self.output_dir = output_dir
        self.detector = ObjectDetector()
        self.mqtt_handler = MQTTHandler(config)
        self.db_handler = DatabaseHandler(config)
        
        # Frame timing for hourly saving
        self.last_frame_save_time = 0
        self.frame_save_interval = 3600  # 3600 seconds = 1 hour
        
        # Create output directory
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def _save_detection(self, annotated_frame, timestamp: str):
        """Saves the detected frame"""
        cleanup_results_folder(self.output_dir, self.config.usage_threshold)
        output_file = f'{self.output_dir}/frame_{timestamp}.jpg'
        cv2.imwrite(output_file, annotated_frame)
    
    def _resize_frame_to_fullhd(self, frame):
        """Reduces frame resolution from 4K to Full HD (1920x1080)"""
        height, width = frame.shape[:2]
        
        # Target resolution: Full HD (1920x1080)
        target_width = 1920
        target_height = 1080
        
        # Only resize if frame is larger than Full HD
        if width > target_width or height > target_height:
            resized_frame = cv2.resize(frame, (target_width, target_height), interpolation=cv2.INTER_AREA)
            print(f"Frame resized from {width}x{height} to {target_width}x{target_height}")
            return resized_frame
        else:
            # Frame is already Full HD or smaller
            return frame
    
    def _save_frame_to_database_if_needed(self, frame):
        """Saves the current frame to database if one hour has passed"""
        current_time = time.time()
        
        if current_time - self.last_frame_save_time >= self.frame_save_interval:
            self.last_frame_save_time = current_time
            success = self.db_handler.save_frame_to_database(frame)
            if success:
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                print(f"Frame saved to database at {timestamp}")
            return success
        
        return False
    
    def _process_detections(self, frame, detections, results):
        """Processes the detections"""
        for class_id, confidence, bbox in detections:
            if confidence > self.config.confidence_threshold:
                # Check ignore zone
                if self.detector.is_in_ignore_zone(bbox, frame.shape, self.config.ignore_zone):
                    continue
                
                # Annotate frame
                annotated_frame = None
                for result in results:
                    annotated_frame = result.plot()
                    break
                
                if annotated_frame is None:
                    continue
                
                # Generate timestamp
                timestamp = time.strftime('%Y-%m-%d_%H-%M-%S-%f')[:-3]
                
                # Save frame
                self._save_detection(annotated_frame, timestamp)
                
                # Save detection image to database
                success = self.db_handler.save_frame_to_database(annotated_frame, confidence)
                if success:
                    print(f"Detection image saved to database (Confidence: {confidence:.2f})")
                else:
                    print("Error saving detection image to database")
                
                # Output information
                class_name = self.detector.CLASS_NAMES.get(class_id, "Unknown")
                print(f'Detected class ID: {class_id}')
                print(f'Detected class name: {class_name}')
                print(f'Detected class confidence: {confidence}')
                
                # Send MQTT message
                self.mqtt_handler.publish_detection(class_name, confidence, timestamp)
    
    def run(self):
        """Main loop for stream processing"""
        while True:
            cap = cv2.VideoCapture(self.config.rtsp_stream_url)
            
            if not cap.isOpened():
                print(f"Error opening RTSP stream: {self.config.rtsp_stream_url}. Retrying in 5 seconds...")
                time.sleep(5)
                continue
            
            print("RTSP stream connection established successfully.")
            
            # Process frames
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Reduce frame resolution from 4K to Full HD
                frame = self._resize_frame_to_fullhd(frame)
                
                # Save frame to database every hour
                self._save_frame_to_database_if_needed(frame)
                
                # Object detection
                detections, results = self.detector.detect_objects(frame)
                
                # Process detections
                if detections:
                    self._process_detections(frame, detections, results)
                
                # Exit on 'q'
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    cap.release()
                    return
            
            cap.release()
        
        print(f'Frames with detected objects are saved in folder "{self.output_dir}".')


class KatzenschreckApp:
    """Main application class"""
    
    def __init__(self):
        self.args = self._parse_arguments()
        self.config = Config('../config.txt')
        self.processor = StreamProcessor(self.config, self.args.output_dir)
    
    def _parse_arguments(self):
        """Parses command line arguments"""
        parser = argparse.ArgumentParser(description="Process RTSP stream and save detected frames.")
        parser.add_argument("output_dir", type=str, help="The folder where detected frames will be saved.")
        return parser.parse_args()
    
    def run(self):
        """Starts the application"""
        self.processor.run()


def main():
    """Main function"""
    app = KatzenschreckApp()
    app.run()


if __name__ == "__main__":
    main()