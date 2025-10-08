"""Object detection using YOLO for cat detection"""

from typing import Optional, List, Tuple
from ultralytics import YOLO
from .hardware_detector import HardwareDetector


class ObjectDetector:
    """YOLO object detection class with automatic hardware detection"""

    CLASS_NAMES = {0: 'Person', 15: 'Cat'}
    TARGET_CLASS_ID = 15  # Cat

    def __init__(self, model_path: Optional[str] = None):
        # Auto-detect optimal model if not specified
        if model_path is None:
            hardware_detector = HardwareDetector()
            model_path, requirements_file = hardware_detector.get_optimal_model()
            print(f"🤖 Auto-detected optimal model: {model_path}")
            print(f"📋 Using requirements: {requirements_file}")
        
        self.model = YOLO(model_path)

    def detect_objects(self, frame) -> Tuple[List[Tuple[int, float, List[float]]],
                                            object]:
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

    def is_in_ignore_zone(self, bbox: List[float], frame_shape: Tuple[int, int],
                          ignore_zone: Optional[List[float]]) -> bool:
        """Checks if the bounding box is in the ignore zone"""
        if not ignore_zone:
            return False

        x1, y1, x2, y2 = bbox
        frame_h, frame_w = frame_shape[:2]

        # Box coordinates as percentage values
        box_coords = self._get_box_percentage_coords(x1, y1, x2, y2, frame_w, frame_h)

        # Ignore zone coordinates
        iz_xmin, iz_ymin, iz_xmax, iz_ymax = ignore_zone

        # Check if box overlaps with ignore zone
        return self._check_box_overlap(box_coords, (iz_xmin, iz_ymin, iz_xmax, iz_ymax))

    def _get_box_percentage_coords(self, x1, y1, x2, y2, frame_w, frame_h):
        """Convert box coordinates to percentage values"""
        return {
            'xmin': x1 / frame_w,
            'ymin': y1 / frame_h,
            'xmax': x2 / frame_w,
            'ymax': y2 / frame_h
        }

    def _check_box_overlap(self, box_coords, ignore_zone):
        """Check if box overlaps with ignore zone"""
        iz_xmin, iz_ymin, iz_xmax, iz_ymax = ignore_zone
        return not (box_coords['xmax'] < iz_xmin or box_coords['xmin'] > iz_xmax or
                   box_coords['ymax'] < iz_ymin or box_coords['ymin'] > iz_ymax)
