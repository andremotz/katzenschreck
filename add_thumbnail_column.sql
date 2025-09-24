-- SQL-Skript zum Hinzufügen der thumbnail_jpeg Spalte zur bestehenden Tabelle
-- Dieses Skript kann ausgeführt werden, um bestehende Datenbanken zu aktualisieren

USE katzenschreck;

-- Thumbnail-Spalte hinzufügen (falls sie noch nicht existiert)
ALTER TABLE detections_images 
ADD COLUMN IF NOT EXISTS thumbnail_jpeg BLOB AFTER blob_jpeg;

-- Beispiel-Abfrage mit Thumbnail
-- SELECT id, camera_name, accuracy, 
--        LENGTH(blob_jpeg) as image_size_bytes, 
--        LENGTH(thumbnail_jpeg) as thumbnail_size_bytes, 
--        created_at 
-- FROM detections_images 
-- ORDER BY created_at DESC 
-- LIMIT 10;
