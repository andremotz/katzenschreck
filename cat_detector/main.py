"""Main application entry point for the cat deterrent system"""

import argparse
import sys
import os

# Add the parent directory to the Python path for absolute imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cat_detector.config import Config
from cat_detector.stream_processor import StreamProcessor


class KatzenschreckApp:  # pylint: disable=too-few-public-methods
    """Main application class"""

    def __init__(self):
        self.args = self._parse_arguments()
        config_path = self._get_config_path()
        self.config = Config(config_path)
        self.processor = StreamProcessor(self.config, self.args.output_dir)

    def _get_config_path(self):
        """Determines the correct config.txt path (Docker or local)"""
        # Check if running in Docker container
        docker_config_path = '/app/config.txt'
        if os.path.exists(docker_config_path):
            return docker_config_path
        # Default to local path
        return '../config.txt'

    def _parse_arguments(self):
        """Parses command line arguments"""
        parser = argparse.ArgumentParser(
            description="Process RTSP stream and save detected frames.")
        parser.add_argument("output_dir", type=str,
                           help="The folder where detected frames will be saved.")
        return parser.parse_args()

    def run(self):
        """Starts the application"""
        self.processor.run()


def main():
    """Main function"""
    app = KatzenschreckApp()
    app.run()


if __name__ == "__main__":
    main()
