-- SQL script to add the thumbnail_jpeg column to the existing table
-- This script can be executed to update existing databases

USE katzenschreck;

-- Add thumbnail column (if it doesn't exist yet)
ALTER TABLE detections_images 
ADD COLUMN IF NOT EXISTS thumbnail_jpeg BLOB AFTER blob_jpeg;

-- Example query with thumbnail
-- SELECT id, camera_name, accuracy, 
--        LENGTH(blob_jpeg) as image_size_bytes, 
--        LENGTH(thumbnail_jpeg) as thumbnail_size_bytes, 
--        created_at 
-- FROM detections_images 
-- ORDER BY created_at DESC 
-- LIMIT 10;
