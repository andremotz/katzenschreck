"""Object detection using YOLO for cat detection"""

from typing import Optional, List, Tuple
from ultralytics import YOLO


class ObjectDetector:
    """YOLO object detection class"""

    CLASS_NAMES = {0: 'Person', 15: 'Cat'}
    TARGET_CLASS_ID = 15  # Cat

    def __init__(self, model_path: str = 'yolo12l.pt'):
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
        box_xmin = x1 / frame_w
        box_ymin = y1 / frame_h
        box_xmax = x2 / frame_w
        box_ymax = y2 / frame_h

        # Ignore zone coordinates
        iz_xmin, iz_ymin, iz_xmax, iz_ymax = ignore_zone

        # Check if box overlaps with ignore zone
        return not (box_xmax < iz_xmin or box_xmin > iz_xmax or
                   box_ymax < iz_ymin or box_ymin > iz_ymax)