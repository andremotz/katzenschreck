-- SQL-Skript zur Erstellung der benötigten Tabelle für das Katzenschreck-System
-- MariaDB/MySQL

-- Datenbank erstellen (falls nicht vorhanden)
CREATE DATABASE IF NOT EXISTS katzenschreck;
USE katzenschreck;

-- Benutzer erstellen (falls nicht vorhanden)
CREATE USER IF NOT EXISTS 'katzenschreck_app'@'localhost' IDENTIFIED BY 'p7eWPjGeIRXtMvCJw--';
GRANT ALL PRIVILEGES ON katzenschreck.* TO 'katzenschreck_app'@'localhost';
FLUSH PRIVILEGES;

-- Tabelle für Frame-Bilder erstellen
CREATE TABLE IF NOT EXISTS detections_images (
    id INT AUTO_INCREMENT PRIMARY KEY,
    camera_name VARCHAR(100) NOT NULL,
    accuracy DECIMAL(5, 4) DEFAULT 1.0000,
    blob_jpeg LONGBLOB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_camera_created (camera_name, created_at),
    INDEX idx_created_at (created_at)
);

-- Beispiel-Abfrage zum Testen
-- SELECT id, camera_name, accuracy, LENGTH(blob_jpeg) as image_size_bytes, created_at 
-- FROM detections_images 
-- ORDER BY created_at DESC 
-- LIMIT 10;
