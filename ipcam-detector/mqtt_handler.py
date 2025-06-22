import paho.mqtt.client as mqtt
import time
import threading


class MQTTHandler:
    def __init__(self, broker_url, broker_port, username, password, topic):
        self.broker_url = broker_url
        self.broker_port = broker_port
        self.username = username
        self.password = password
        self.topic = topic
        self.client = None
        self.connected = False
        self.ping_thread = None
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT broker successfully")
            self.connected = True
        else:
            print(f"Failed to connect to MQTT broker with code: {rc}")
            self.connected = False

    def on_disconnect(self, client, userdata, rc):
        print(f"Disconnected from MQTT broker with code: {rc}")
        self.connected = False

    def connect(self):
        try:
            print(f"Attempting to connect to MQTT broker at {self.broker_url}:{self.broker_port}")
            self.client = mqtt.Client()
            self.client.username_pw_set(self.username, self.password)
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.connect(self.broker_url, self.broker_port, 60)
            self.client.loop_start()
            print("MQTT connection initiated successfully")
            return True
        except Exception as e:
            print(f"Error connecting to MQTT broker: {e}")
            self.connected = False
            return False

    def send_message(self, subtopic, message):
        if not self.connected:
            print("Attempting to reconnect to MQTT broker...")
            self.connect()
        
        if self.connected:
            try:
                full_topic = f'{self.topic}/{subtopic}'
                self.client.publish(full_topic, message)
                return True
            except Exception as e:
                print(f"Error sending MQTT message: {e}")
                self.connected = False
                return False
        else:
            print("Could not send MQTT message - not connected to broker")
            return False

    def _ping_loop(self):
        print("MQTT ping thread started")
        while True:
            time.sleep(30)
            print(f"Ping check - mqtt_connected: {self.connected}")
            if not self.connected:
                print("Attempting to reconnect to MQTT broker...")
                self.connect()
            if self.connected:
                try:
                    current_timestamp = int(time.time())
                    print(f"Sending ping to {self.topic}/ping at {current_timestamp}")
                    self.client.publish(f'{self.topic}/ping', f'{{"timestamp": {current_timestamp}}}')
                    print("Ping sent successfully")
                except Exception as e:
                    print(f"Error sending MQTT ping: {e}")
                    self.connected = False
            else:
                print("Cannot send ping - not connected to MQTT broker")

    def start_ping_thread(self):
        self.ping_thread = threading.Thread(target=self._ping_loop)
        self.ping_thread.daemon = True
        self.ping_thread.start()

    def is_connected(self):
        return self.connected 