-- Schnelle Lösung für max_allowed_packet Problem
-- Dieses Skript direkt in MariaDB/MySQL ausführen

-- Aktuelle Einstellung anzeigen
SELECT 'Aktuelle max_allowed_packet Einstellung:' AS info;
SHOW VARIABLES LIKE 'max_allowed_packet';

-- Neue Einstellung setzen (256MB für HD/4K-Bilder)
SET GLOBAL max_allowed_packet = 268435456;

-- Bestätigung anzeigen
SELECT 'Neue max_allowed_packet Einstellung:' AS info;
SHOW VARIABLES LIKE 'max_allowed_packet';

-- Zusätzliche nützliche Informationen
SELECT 'Weitere relevante Einstellungen:' AS info;
SHOW VARIABLES WHERE Variable_name IN (
    'innodb_buffer_pool_size',
    'wait_timeout',
    'interactive_timeout'
);

-- Erfolgsmeldung
SELECT 'max_allowed_packet erfolgreich auf 256MB erhöht!' AS status;
SELECT 'WICHTIG: Für permanente Änderung die my.cnf bearbeiten!' AS hinweis;
