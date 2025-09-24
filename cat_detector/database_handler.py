"""Database handler for MariaDB operations"""

import cv2
import mysql.connector
from mysql.connector import Error
from .config import Config


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

            print(f"Frame successfully saved to database "
                  f"(Original size: {len(jpeg_data)} bytes, "
                  f"Thumbnail: {len(thumbnail_data)} bytes)")
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
            thumbnail = cv2.resize(frame, (target_width, target_height),
                                  interpolation=cv2.INTER_AREA)

            # Convert thumbnail to JPEG format
            success, thumbnail_buffer = cv2.imencode(
                '.jpg', thumbnail, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if not success:
                return None

            return thumbnail_buffer.tobytes()

        except (cv2.error, ValueError, TypeError) as e:
            print(f"Error creating thumbnail: {e}")
            return None