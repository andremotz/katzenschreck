# MariaDB Konfiguration für Katzenschreck

## Problem: max_allowed_packet zu klein

Der Fehler "Got a packet bigger than 'max_allowed_packet' bytes" tritt auf, wenn JPEG-Bilder größer sind als das MariaDB-Limit (Standard: 16MB).

## ⚡ Schnelle Lösung: Sofort anwenden

```sql
-- Verbindung zur MariaDB als root
mysql -u root -p

-- Max packet size auf 256MB erhöhen (ausreichend für 4K-Bilder)
SET GLOBAL max_allowed_packet = 268435456;

-- Prüfen ob erfolgreich
SHOW VARIABLES LIKE 'max_allowed_packet';
```

## 🔧 Permanente Lösung: Konfigurationsdatei anpassen

### Ubuntu/Debian:
Datei: `/etc/mysql/mariadb.conf.d/50-server.cnf`

### CentOS/RHEL:
Datei: `/etc/my.cnf.d/server.cnf`

### macOS (Homebrew):
Datei: `/opt/homebrew/etc/my.cnf`

Füge folgende Zeilen unter `[mysqld]` hinzu:
```
[mysqld]
# Für HD/4K-Bilder (256MB)
max_allowed_packet = 256M

# Zusätzliche Optimierungen für BLOB-Storage
innodb_buffer_pool_size = 512M
innodb_log_file_size = 256M
wait_timeout = 600
```

## 📋 Schritt-für-Schritt Anleitung

### 1. Sofortige Anwendung (temporär bis Neustart)
```bash
# MariaDB/MySQL als root verbinden
mysql -u root -p

# In der MySQL-Konsole:
SET GLOBAL max_allowed_packet = 268435456;  -- 256MB
SHOW VARIABLES LIKE 'max_allowed_packet';
EXIT;
```

### 2. Permanente Konfiguration
```bash
# Konfigurationsdatei bearbeiten (Ubuntu/Debian)
sudo nano /etc/mysql/mariadb.conf.d/50-server.cnf

# Oder für andere Systeme
sudo nano /etc/my.cnf
```

### 3. MariaDB neustarten
```bash
sudo systemctl restart mariadb
# oder
sudo systemctl restart mysql
```

## 🔍 Problemdiagnose

```sql
-- Aktuelle Limits prüfen
SHOW VARIABLES LIKE 'max_allowed_packet';
SHOW VARIABLES LIKE 'innodb_buffer_pool_size';

-- Datenbank-Verbindung testen
SELECT CONNECTION_ID(), USER(), DATABASE();
```

## MariaDB neustarten

Nach Konfigurationsänderungen MariaDB neustarten:

```bash
# Ubuntu/Debian
sudo systemctl restart mariadb

# CentOS/RHEL
sudo systemctl restart mysql

# macOS (Homebrew)
brew services restart mariadb
```

## Empfohlene Einstellungen

- **max_allowed_packet**: 64MB (für HD-Bilder ausreichend)
- **innodb_buffer_pool_size**: 256MB+ (für bessere Performance)
- **wait_timeout**: 600 (10 Minuten für längere Sessions)
