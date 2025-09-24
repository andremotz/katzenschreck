-- SQL script for creating the required table for the cat deterrent system
-- MariaDB/MySQL

-- Create database (if not exists)
CREATE DATABASE IF NOT EXISTS katzenschreck;
USE katzenschreck;

-- Create user (if not exists)
CREATE USER IF NOT EXISTS 'katzenschreck_app'@'%' IDENTIFIED BY '<password>';
GRANT ALL PRIVILEGES ON katzenschreck.* TO 'katzenschreck_app'@'%';
FLUSH PRIVILEGES;

-- Create table for frame images
CREATE TABLE IF NOT EXISTS detections_images (
    id INT AUTO_INCREMENT PRIMARY KEY,
    camera_name VARCHAR(100) NOT NULL,
    accuracy DECIMAL(5, 4) DEFAULT 1.0000,
    blob_jpeg LONGBLOB NOT NULL,
    thumbnail_jpeg BLOB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_camera_created (camera_name, created_at),
    INDEX idx_created_at (created_at)
);

-- Example query for testing
-- SELECT id, camera_name, accuracy, 
--        LENGTH(blob_jpeg) as image_size_bytes, 
--        LENGTH(thumbnail_jpeg) as thumbnail_size_bytes, 
--        created_at 
-- FROM detections_images 
-- ORDER BY created_at DESC 
-- LIMIT 10;
