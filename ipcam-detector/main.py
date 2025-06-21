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


def setup_rtsp_capture(rtsp_url):
    """Setup RTSP capture with robust settings for network issues"""
    print(f"Original RTSP URL: {rtsp_url}")
    
    # Set OpenCV backend to FFMPEG for better RTSP handling
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
    
    # Try the original URL first without modification
    cap = cv2.VideoCapture(rtsp_url)
    
    # Set buffer size to minimum to reduce latency
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    # Set frame rate to reduce processing load
    cap.set(cv2.CAP_PROP_FPS, 10)
    
    # Set timeout for connection
    cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
    cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)
    
    return cap


def main():
    print("Starting IP Camera Detection System...")
    
    # Initialize configuration
    print("Loading configuration...")
    config_handler = ConfigHandler()
    config = config_handler.load_config('../config.txt')
    output_dir = config_handler.get_output_dir()
    print(f"Configuration loaded. Output directory: {output_dir}")
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
    
    # Initialize MQTT handler
    print("Initializing MQTT connection...")
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
    print(f"MQTT connection status: {mqtt_handler.is_connected()}")
    mqtt_handler.start_ping_thread()
    
    # Initialize detection handler
    print("Initializing detection handler...")
    detection_handler = DetectionHandler(
        confidence_threshold=config['confidence_threshold'],
        ignore_zone=config['ignore_zone']
    )
    print("Detection handler initialized successfully!")
    
    print("Starting main processing loop...")
    
    # Main processing loop
    consecutive_errors = 0
    max_consecutive_errors = 5
    
    while True:
        print(f"Connecting to RTSP stream: {config['rtsp_stream_url']}")
        try:
            cap = setup_rtsp_capture(config['rtsp_stream_url'])
            
            # Check if stream opened successfully
            if not cap.isOpened():
                consecutive_errors += 1
                print(f"Fehler beim Öffnen des RTSP-Streams: {config['rtsp_stream_url']}. Versuche erneut in 5 Sekunden... (Error {consecutive_errors}/{max_consecutive_errors})")
                if consecutive_errors >= max_consecutive_errors:
                    print("Zu viele aufeinanderfolgende Fehler. Warte 30 Sekunden vor erneutem Versuch...")
                    time.sleep(30)
                    consecutive_errors = 0
                else:
                    time.sleep(5)
                continue
            
            print("Verbindung zum RTSP-Stream erfolgreich aufgebaut.")
            print("Starting frame processing...")
            
            frame_count = 0
            consecutive_errors = 0  # Reset error counter on successful connection
            
            # Process frames
            while cap.isOpened():
                try:
                    # Get the most recent frame by clearing buffer first
                    ret, frame = get_latest_frame(cap)
                    if not ret:
                        print("Fehler beim Lesen des Frames. Versuche erneut...")
                        consecutive_errors += 1
                        if consecutive_errors >= max_consecutive_errors:
                            print("Zu viele Frame-Fehler. Starte Verbindung neu...")
                            break
                        time.sleep(1)
                        continue
                    
                    consecutive_errors = 0  # Reset error counter on successful frame read
                    frame_count += 1
                    if frame_count % 30 == 0:  # Print status every 30 frames
                        print(f"Processed {frame_count} frames...")
                    
                    # Process detections
                    detection_handler.process_detections(frame, mqtt_handler, output_dir, config['usage_threshold'], config['save_all_frames'])
                    
                    # Check for quit command
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                        
                except Exception as e:
                    print(f"Error during frame processing: {e}")
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        print("Zu viele Verarbeitungsfehler. Starte Verbindung neu...")
                        break
                    time.sleep(1)
            
            cap.release()
            print("Stream connection lost. Reconnecting...")
            time.sleep(2)  # Brief pause before reconnecting
            
        except Exception as e:
            consecutive_errors += 1
            print(f"Error during connection setup: {e}")
            if consecutive_errors >= max_consecutive_errors:
                print("Zu viele Verbindungsfehler. Warte 30 Sekunden vor erneutem Versuch...")
                time.sleep(30)
                consecutive_errors = 0
            else:
                time.sleep(5)
    
    print(f'Frames mit erkannten Objekten sind im Ordner "{output_dir}" gespeichert.')


if __name__ == "__main__":
    main() 