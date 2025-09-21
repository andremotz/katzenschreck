# MariaDB Konfiguration für Katzenschreck

## Problem: max_allowed_packet zu klein

Falls der Fehler "Got a packet bigger than 'max_allowed_packet' bytes" auftritt, kann die MariaDB-Konfiguration angepasst werden.

## Lösung 1: Temporär für aktuelle Session

```sql
SET GLOBAL max_allowed_packet = 64*1024*1024; -- 64MB
```

## Lösung 2: Permanent in MariaDB-Konfiguration

### Ubuntu/Debian:
Datei: `/etc/mysql/mariadb.conf.d/50-server.cnf`

### CentOS/RHEL:
Datei: `/etc/my.cnf.d/server.cnf`

### macOS (Homebrew):
Datei: `/opt/homebrew/etc/my.cnf`

Füge folgende Zeile unter `[mysqld]` hinzu:
```
[mysqld]
max_allowed_packet = 64M
```

## Lösung 3: Über SQL prüfen und setzen

```sql
-- Aktuelle Einstellung prüfen
SHOW VARIABLES LIKE 'max_allowed_packet';

-- Neu setzen (bis zum Neustart)
SET GLOBAL max_allowed_packet = 67108864; -- 64MB in Bytes

-- Nach Änderung prüfen
SHOW VARIABLES LIKE 'max_allowed_packet';
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
