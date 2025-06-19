import cv2
import time
from ultralytics import YOLO


class DetectionHandler:
    def __init__(self, confidence_threshold=0.5, ignore_zone=None):
        self.confidence_threshold = confidence_threshold
        self.ignore_zone = ignore_zone
        self.model = None  # Lazy loading
        self.class_names = {0: 'Person', 15: 'Cat'}
        
    def _load_model(self):
        """Load YOLO model lazily when first needed"""
        if self.model is None:
            print("Loading YOLO model... This may take a few minutes on first run.")
            try:
                self.model = YOLO('yolo11n.pt')
                print("YOLO model loaded successfully!")
            except Exception as e:
                print(f"Error loading YOLO model: {e}")
                raise
        
    def is_in_ignore_zone(self, box, frame):
        """Check if detection box is in ignore zone"""
        if not self.ignore_zone:
            return False
            
        # Box-Koordinaten (x1, y1, x2, y2) in Pixel
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        frame_h, frame_w = frame.shape[:2]
        
        # Box-Koordinaten als Prozentwerte
        box_xmin = x1 / frame_w
        box_ymin = y1 / frame_h
        box_xmax = x2 / frame_w
        box_ymax = y2 / frame_h
        
        # Ignore-Zone-Koordinaten
        iz_xmin, iz_ymin, iz_xmax, iz_ymax = self.ignore_zone
        
        # Prüfe, ob sich die Box mit der Ignore-Zone überschneidet
        return not (box_xmax < iz_xmin or box_xmin > iz_xmax or box_ymax < iz_ymin or box_ymin > iz_ymax)
        
    def save_frame(self, frame, output_dir, usage_threshold, prefix="frame"):
        """Save a frame to disk"""
        # Vor dem Speichern: Speicherplatz prüfen und ggf. alte Bilder löschen
        from results_cleanup import cleanup_results_folder
        cleanup_results_folder(output_dir, usage_threshold)
        
        # Generate timestamp
        current_date_time = time.strftime('%Y-%m-%d_%H-%M-%S-%f')[:-3]
        
        # Speichere das Frame
        output_file = f'{output_dir}/{prefix}_{current_date_time}.jpg'
        cv2.imwrite(output_file, frame)
        print(f"Frame saved: {output_file}")
        
    def process_detections(self, frame, mqtt_handler, output_dir, usage_threshold, save_all_frames=False):
        """Process frame for detections and handle results"""
        # Load model if not already loaded
        self._load_model()
        
        # Save frame if save_all_frames is enabled
        if save_all_frames:
            self.save_frame(frame, output_dir, usage_threshold, "all_frame")
        
        try:
            results = self.model(frame)
            detections_found = False
            
            for result in results:
                for box in result.boxes:
                    # Extract the class ID from the tensor
                    class_id = int(box.cls.item())
                    
                    # Klasse 0 ist 'Person' und Klasse 15 ist 'Katze' (COCO-Datensatzklassennummern)
                    if class_id == 0 or class_id == 15:
                        # mache nur weiter, wenn die accuracy über dem konfigurierten Schwellenwert ist
                        if box.conf > self.confidence_threshold:
                            # Prüfe, ob die Box in der Ignore-Zone liegt
                            if self.is_in_ignore_zone(box, frame):
                                continue  # Box liegt (ganz oder teilweise) in der Ignore-Zone, also überspringen
                                
                            detections_found = True
                            self._handle_detection(box, result, frame, mqtt_handler, output_dir, usage_threshold)
                            
            return detections_found
        except Exception as e:
            print(f"Error during detection processing: {e}")
            return False
        
    def _handle_detection(self, box, result, frame, mqtt_handler, output_dir, usage_threshold):
        """Handle a single detection"""
        # Zeichne die erkannten Objekte auf dem Frame
        annotated_frame = result.plot()

        # this variable returns the current date and time in the format 'YYYY-MM-DD_HH-MM-SS-MS'
        current_date_time = time.strftime('%Y-%m-%d_%H-%M-%S-%f')[:-3]

        # Vor dem Speichern: Speicherplatz prüfen und ggf. alte Bilder löschen
        from results_cleanup import cleanup_results_folder
        cleanup_results_folder(output_dir, usage_threshold)
        
        # Speichere das Frame mit den erkannten Objekten
        output_file = f'{output_dir}/frame_{current_date_time}.jpg'
        cv2.imwrite(output_file, annotated_frame)

        # Print the class ID to the terminal
        detected_class_id = int(box.cls.item())
        detected_class_name = self.class_names.get(detected_class_id, "Unknown")
        detected_class_confidence = box.conf.item()
        print(f'Detected class ID: {detected_class_id}')
        print(f'Detected class name: {detected_class_name}')
        print(f'Detected class confidence: {detected_class_confidence}')

        # Send MQTT message
        message = f'{{"time": "{current_date_time}", "class": "{detected_class_name}", "confidence": "{detected_class_confidence}"}}'
        mqtt_handler.send_message(detected_class_name, message) 