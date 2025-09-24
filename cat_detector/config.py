"""Configuration management for the cat deterrent system"""


class Config:  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    """Configuration class for the cat deterrent system"""

    def __init__(self, config_file_path: str):
        self.config_file_path = config_file_path
        self._load_config()
        self._validate_config()

    def _load_config(self):
        """Loads configuration from file"""
        config = {}
        with open(self.config_file_path, 'r', encoding='utf-8') as file:
            for line in file:
                if '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()

        # RTSP and MQTT configuration
        self.rtsp_stream_url = config.get('rtsp_stream_url')
        self.mqtt_broker_url = config.get('mqtt_broker_url')
        self.mqtt_broker_port = int(config.get('mqtt_broker_port', 1883))
        self.mqtt_topic = config.get('mqtt_topic')
        self.mqtt_username = config.get('mqtt_username')
        self.mqtt_password = config.get('mqtt_password')

        # Detection configuration
        self.confidence_threshold = float(config.get('confidence_threshold', 0.5))
        self.usage_threshold = float(config.get('usage_threshold', 0.8))

        # Database configuration
        self.db_host = config.get('db_host', 'localhost')
        self.db_user = config.get('db_user', 'katzenschreck_app')
        self.db_password = config.get('db_password', 'p7eWPjGeIRXtMvCJw--')
        self.db_database = config.get('db_database', 'katzenschreck')
        self.camera_name = config.get('camera_name', 'cam_garten')

        # Ignore zone configuration
        ignore_zone_str = config.get('ignore_zone')
        if ignore_zone_str:
            self.ignore_zone = [float(x) for x in ignore_zone_str.split(',')]
        else:
            self.ignore_zone = None

    def _validate_config(self):
        """Validates the configuration"""
        required_fields = [
            ('rtsp_stream_url', self.rtsp_stream_url),
            ('mqtt_broker_url', self.mqtt_broker_url),
            ('mqtt_topic', self.mqtt_topic),
            ('mqtt_username', self.mqtt_username),
            ('mqtt_password', self.mqtt_password)
        ]

        for field_name, field_value in required_fields:
            if not field_value:
                raise ValueError(f"{field_name} not found in config.txt")
