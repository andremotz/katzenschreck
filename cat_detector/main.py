"""Main application entry point for the cat deterrent system"""

import argparse
from .config import Config
from .stream_processor import StreamProcessor


class KatzenschreckApp:  # pylint: disable=too-few-public-methods
    """Main application class"""

    def __init__(self):
        self.args = self._parse_arguments()
        self.config = Config('../config.txt')
        self.processor = StreamProcessor(self.config, self.args.output_dir)

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