import argparse


class ConfigHandler:
    def __init__(self):
        self.parser = None
        self.args = None
        self.config = {}
        
    def setup_argument_parser(self):
        self.parser = argparse.ArgumentParser(description="RTSP-Stream verarbeiten und erkannte Frames speichern.")
        self.parser.add_argument("output_dir", type=str, help="Der Ordner, in dem die erkannten Frames gespeichert werden.")
        
    def parse_arguments(self):
        if not self.parser:
            self.setup_argument_parser()
        self.args = self.parser.parse_args()
        return self.args
        
    def read_config_file(self, file_path):
        """Read configuration from config.txt file"""
        config = {}
        try:
            with open(file_path, 'r') as file:
                for line in file:
                    if '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        except Exception as e:
            raise Exception(f"Error reading configuration file: {e}")
        return config
        
    def load_config(self, config_file_path):
        """Load and validate configuration"""
        self.config = self.read_config_file(config_file_path)
        
        # Extract and validate required values
        config_data = {
            'rtsp_stream_url': self.config.get('rtsp_stream_url'),
            'mqtt_broker_url': self.config.get('mqtt_broker_url'),
            'mqtt_broker_port': int(self.config.get('mqtt_broker_port', 1883)),
            'mqtt_topic': self.config.get('mqtt_topic'),
            'mqtt_username': self.config.get('mqtt_username'),
            'mqtt_password': self.config.get('mqtt_password'),
            'confidence_threshold': float(self.config.get('confidence_threshold', 0.5)),
            'usage_threshold': float(self.config.get('usage_threshold', 0.8)),
            'save_all_frames': self.config.get('save_all_frames', 'false').lower() == 'true'
        }
        
        # Parse ignore zone if present
        ignore_zone_str = self.config.get('ignore_zone')
        if ignore_zone_str:
            config_data['ignore_zone'] = [float(x) for x in ignore_zone_str.split(',')]
        else:
            config_data['ignore_zone'] = None
            
        # Validate required fields
        required_fields = ['rtsp_stream_url', 'mqtt_broker_url', 'mqtt_topic', 'mqtt_username', 'mqtt_password']
        for field in required_fields:
            if not config_data[field]:
                raise ValueError(f"{field} not found in config.txt")
                
        return config_data
        
    def get_output_dir(self):
        """Get output directory from command line arguments"""
        if not self.args:
            self.parse_arguments()
        return self.args.output_dir 