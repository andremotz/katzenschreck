import cv2
import os
import time
from mqtt_handler import MQTTHandler
from config_handler import ConfigHandler
from detection_handler import DetectionHandler


def get_latest_frame(cap):
    """Get the most recent frame by clearing the buffer first"""
    # Clear the buffer by grabbing all available frames
    while True:
        grabbed = cap.grab()
        if not grabbed:
            break
    
    # Now read the most recent frame
    ret, frame = cap.read()
    return ret, frame


def main():
    # Initialize configuration
    config_handler = ConfigHandler()
    config = config_handler.load_config('../config.txt')
    output_dir = config_handler.get_output_dir()
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Initialize MQTT handler
    mqtt_handler = MQTTHandler(
        config['mqtt_broker_url'],
        config['mqtt_broker_port'],
        config['mqtt_username'],
        config['mqtt_password'],
        config['mqtt_topic']
    )
    
    # Connect to MQTT and start ping thread
    mqtt_handler.connect()
    time.sleep(2)  # Wait for connection to establish
    print(f"Initial MQTT connection status: {mqtt_handler.is_connected()}")
    mqtt_handler.start_ping_thread()
    
    # Initialize detection handler
    detection_handler = DetectionHandler(
        confidence_threshold=config['confidence_threshold'],
        ignore_zone=config['ignore_zone']
    )
    
    # Main processing loop
    while True:
        cap = cv2.VideoCapture(config['rtsp_stream_url'])
        
        # Set buffer size to minimum to reduce latency
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        # Check if stream opened successfully
        if not cap.isOpened():
            print(f"Fehler beim Öffnen des RTSP-Streams: {config['rtsp_stream_url']}. Versuche erneut in 5 Sekunden...")
            time.sleep(5)
            continue
        
        print("Verbindung zum RTSP-Stream erfolgreich aufgebaut.")
        
        # Process frames
        while cap.isOpened():
            # Get the most recent frame by clearing buffer first
            ret, frame = get_latest_frame(cap)
            if not ret:
                print("Fehler beim Lesen des Frames. Versuche erneut...")
                break
            
            # Process detections
            detection_handler.process_detections(frame, mqtt_handler, output_dir, config['usage_threshold'], config['save_all_frames'])
            
            # Check for quit command
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
    
    print(f'Frames mit erkannten Objekten sind im Ordner "{output_dir}" gespeichert.')


if __name__ == "__main__":
    main() 