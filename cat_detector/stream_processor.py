"""Video stream processing for the cat deterrent system"""

import os
import time
import cv2
from .config import Config
from .object_detector import ObjectDetector
from .mqtt_handler import MQTTHandler
from .database_handler import DatabaseHandler
from .results_cleanup import cleanup_results_folder


class StreamProcessor:  # pylint: disable=too-few-public-methods
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
            resized_frame = cv2.resize(frame, (target_width, target_height),
                                     interpolation=cv2.INTER_AREA)
            print(f"Frame resized from {width}x{height} to "
                  f"{target_width}x{target_height}")
            return resized_frame
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
                if self.detector.is_in_ignore_zone(bbox, frame.shape,
                                                 self.config.ignore_zone):
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
                success = self.db_handler.save_frame_to_database(
                    annotated_frame, confidence)
                if success:
                    print(f"Detection image saved to database "
                          f"(Confidence: {confidence:.2f})")
                else:
                    print("Error saving detection image to database")

                # Output information
                class_name = self.detector.CLASS_NAMES.get(class_id, "Unknown")
                print(f'Detected class ID: {class_id}')
                print(f'Detected class name: {class_name}')
                print(f'Detected class confidence: {confidence}')

                # Send MQTT message
                self.mqtt_handler.publish_detection(class_name, confidence,
                                                   timestamp)

    def run(self):
        """Main loop for stream processing"""
        while True:
            cap = cv2.VideoCapture(self.config.rtsp_stream_url)

            if not cap.isOpened():
                print(f"Error opening RTSP stream: "
                      f"{self.config.rtsp_stream_url}. Retrying in 5 seconds...")
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

        print(f'Frames with detected objects are saved in folder '
              f'"{self.output_dir}".')
