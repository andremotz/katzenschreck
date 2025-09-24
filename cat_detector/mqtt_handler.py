"""MQTT communication handler for the cat deterrent system"""

import time
import json
import threading
import paho.mqtt.client as mqtt
from .config import Config


class MQTTHandler:  # pylint: disable=too-few-public-methods
    """MQTT handler for communication with MQTT broker"""

    def __init__(self, config: Config):
        self.config = config
        self.ping_thread = None
        self._start_ping_thread()

    def _start_ping_thread(self):
        """Starts the MQTT ping thread"""
        self.ping_thread = threading.Thread(target=self._mqtt_ping)
        self.ping_thread.daemon = True
        self.ping_thread.start()

    def _mqtt_ping(self):
        """Sends a ping to the MQTT broker every 30 seconds"""
        while True:
            time.sleep(30)
            client = mqtt.Client()
            client.username_pw_set(self.config.mqtt_username,
                                  self.config.mqtt_password)
            try:
                client.connect(self.config.mqtt_broker_url,
                              self.config.mqtt_broker_port, 60)
                client.loop_start()
                extended_topic = f'{self.config.mqtt_topic}/ping'
                current_timestamp = int(time.time())
                client.publish(extended_topic,
                              json.dumps({"timestamp": current_timestamp}))
                client.loop_stop()
                client.disconnect()
            except (mqtt.MQTTException, ConnectionError, OSError) as e:
                print(f"MQTT Ping Error: {e}")

    def publish_detection(self, class_name: str, confidence: float,
                         timestamp: str):
        """Sends a detection message to the MQTT broker"""
        client = mqtt.Client()
        client.username_pw_set(self.config.mqtt_username,
                              self.config.mqtt_password)

        try:
            client.connect(self.config.mqtt_broker_url,
                          self.config.mqtt_broker_port, 60)
            extended_topic = f'{self.config.mqtt_topic}/{class_name}'
            message = json.dumps({
                "time": timestamp,
                "class": class_name,
                "confidence": confidence
            })
            client.publish(extended_topic, message)
            client.disconnect()
        except (mqtt.MQTTException, ConnectionError, OSError) as e:
            print(f"MQTT Publish Error: {e}")
