# Katzenschreck System Architecture

## High-Level Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   IP Camera     │    │  Katzenschreck  │    │   MariaDB       │    │  Schreckmonitor │
│  (RTSP Stream)  │───▶│     System      │───▶│   Database      │───▶│   Desktop-App   │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │  MQTT Broker    │
                       │  (Notifications)│
                       └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │  Smart Home     │
                       │  Integration    │
                       │ (Sprinkler etc.)│
                       └─────────────────┘
```

## Detailed System Architecture

```mermaid
graph TB
    %% Input Layer
    Camera[IP Camera<br/>RTSP Stream]
    
    %% Core Application Layer
    subgraph "Katzenschreck Application"
        Main[main.py<br/>Entry Point]
        Config[config.py<br/>Configuration Manager]
        
        subgraph "Processing Pipeline"
            Stream[stream_processor.py<br/>Main Processing Loop]
            Detector[object_detector.py<br/>YOLO Detection]
            DB[database_handler.py<br/>Database Operations]
            MQTT[mqtt_handler.py<br/>MQTT Communication]
        end
    end
    
    %% Storage Layer
    subgraph "Data Storage"
        MariaDB[(MariaDB Database<br/>Images & Metadata)]
        FileSystem[File System<br/>Detection Images]
    end
    
    %% External Services
    MQTTBroker[MQTT Broker<br/>Message Queue]
    SmartHome[Smart Home Systems<br/>Automation Triggers]
    
    %% Data Flow
    Camera -->|RTSP Stream| Stream
    Main --> Config
    Main --> Stream
    
    Stream --> Detector
    Stream --> DB
    Stream --> MQTT
    Stream --> FileSystem
    
    Config -.-> Stream
    Config -.-> DB
    Config -.-> MQTT
    
    DB --> MariaDB
    MQTT --> MQTTBroker
    MQTTBroker --> SmartHome
    
    %% Styling
    classDef input fill:#e1f5fe
    classDef processing fill:#f3e5f5
    classDef storage fill:#e8f5e8
    classDef external fill:#fff3e0
    
    class Camera input
    class Main,Config,Stream,Detector,DB,MQTT processing
    class MariaDB,FileSystem storage
    class MQTTBroker,SmartHome external
```

## Component Details

### Core Modules

#### 1. **main.py** - Application Entry Point
- Argument parsing
- Application initialization
- Error handling and logging

#### 2. **config.py** - Configuration Management
- Configuration file parsing
- Environment variable handling
- Parameter validation

#### 3. **stream_processor.py** - Main Processing Engine
- RTSP stream handling
- Frame processing coordination
- Error recovery and reconnection

#### 4. **object_detector.py** - AI Detection Core
- YOLO model integration
- Cat detection algorithms
- Ignore zone filtering
- Confidence threshold management

#### 5. **database_handler.py** - Data Persistence
- MariaDB connection management
- Image storage (original + thumbnails)
- Metadata recording
- Connection pooling

#### 6. **mqtt_handler.py** - Real-time Communications
- MQTT broker connection
- Detection event publishing
- Health monitoring (ping)
- Message formatting

### Data Flow

1. **Input**: IP Camera streams video via RTSP
2. **Processing**: Stream processor captures frames
3. **Detection**: YOLO analyzes frames for cats
4. **Storage**: Positive detections stored in database + filesystem
5. **Notification**: MQTT messages sent to smart home systems
6. **Action**: External systems (sprinklers) triggered

### Storage Schema

```
detections_images Table:
├── id (PRIMARY KEY)
├── camera_name (VARCHAR)
├── accuracy (DECIMAL) - 0.0 for monitoring, >0.0 for detections
├── blob_jpeg (LONGBLOB) - Original image
├── thumbnail_jpeg (BLOB) - 300px thumbnail
└── created_at (TIMESTAMP)
```

## Deployment Architecture

### Option A: Native Deployment
```
┌─────────────────────────────────┐
│         Host System             │
│  ┌─────────────────────────────┐│
│  │    Python Virtual Env       ││
│  │  ┌─────────────────────────┐││
│  │  │   Katzenschreck App     │││
│  │  └─────────────────────────┘││
│  └─────────────────────────────┘│
│  ┌─────────────────────────────┐│
│  │      MariaDB Server         ││
│  └─────────────────────────────┘│
└─────────────────────────────────┘
```

### Option B: Docker Deployment
```
┌─────────────────────────────────┐
│         Docker Host             │
│  ┌─────────────────────────────┐│
│  │   Katzenschreck Container   ││
│  │  ┌─────────────────────────┐││
│  │  │     Application         │││
│  │  │   + Dependencies        │││
│  │  └─────────────────────────┘││
│  └─────────────────────────────┘│
│  ┌─────────────────────────────┐│
│  │   MariaDB Container         ││
│  └─────────────────────────────┘│
└─────────────────────────────────┘
```

## Integration Points

### External Systems
- **MQTT Brokers**: Mosquitto, HiveMQ, AWS IoT Core
- **Smart Home**: Home Assistant, OpenHAB, NodeRED
- **Cameras**: Any RTSP-compatible IP camera
- **Databases**: MariaDB, MySQL (compatible)

### Network Requirements
- **RTSP**: Camera stream access
- **MQTT**: Port 1883 (unencrypted) or 8883 (TLS)
- **Database**: Port 3306 (MariaDB/MySQL)
- **HTTP/HTTPS**: Optional for web interfaces

## Performance Characteristics

- **Frame Processing**: ~1-5 FPS (depending on hardware)
- **Detection Latency**: <2 seconds from capture to MQTT
- **Storage**: ~100KB per detection (with thumbnail)
- **CPU Usage**: Moderate (YOLO inference)
- **Memory**: ~500MB-2GB (model dependent)

## Security Considerations

- Database credentials in configuration
- MQTT authentication required
- RTSP stream credentials
- File system permissions
- Network isolation recommended
