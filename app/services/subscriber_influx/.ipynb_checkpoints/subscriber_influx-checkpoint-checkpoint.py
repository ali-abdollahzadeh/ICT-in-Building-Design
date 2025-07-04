import os
import paho.mqtt.client as PahoMQTT
import time
import json
from influxdb import InfluxDBClient

class MySubscriber:
    def __init__(self, clientID, topic=None):
        self.clientID = clientID
        # create an instance of paho.mqtt.client
        self._paho_mqtt = PahoMQTT.Client(clientID, False) 

        # register the callback
        self._paho_mqtt.on_connect = self.myOnConnect
        self._paho_mqtt.on_message = self.myOnMessageReceived
        topic=os.environ.get('MQTT_TOPIC', None)
        if topic is None:
            self.topic = 'ict4bd'
        else:
            self.topic = topic

        # Use environment variables for hosts
        self.messageBroker = os.environ.get('MQTT_BROKER_HOST', 'localhost')
        influxdb_host = os.environ.get('INFLUXDB_HOST', 'localhost')
        print(self.messageBroker)
        # Initialize InfluxDB client
        DBNAME=os.environ.get('INFLUXDB_DB', clientID)
        self.client = InfluxDBClient(influxdb_host, 8086, 'root', 'root', DBNAME)
        if {'name': DBNAME} not in self.client.get_list_database():
            self.client.create_database(DBNAME)

    def start(self):
        try:
            # manage connection to broker
            self._paho_mqtt.connect(self.messageBroker, 1883)
            self._paho_mqtt.loop_start()
            # subscribe for a topic
            self._paho_mqtt.subscribe(self.topic, 2)
            print(f"Subscribed to topic '{self.topic}'")
        except Exception as e:
            print(f"Error connecting to MQTT broker: {e}")
            self.stop()

    def stop(self):
        self._paho_mqtt.unsubscribe(self.topic)
        self._paho_mqtt.loop_stop()
        self._paho_mqtt.disconnect()

    def myOnConnect(self, paho_mqtt, userdata, flags, rc):
        print(f"Connected to {self.messageBroker} with result code: {rc}")

    def myOnMessageReceived(self, paho_mqtt, userdata, msg):
        # A new message is received
        print(f"Topic: '{msg.topic}', QoS: '{msg.qos}' Message: '{msg.payload}'")
        try:
            data = json.loads(msg.payload)
            json_body = [
                {
                    "measurement": data['measurement'],
                    "tags": {
                        "node": data['node'],
                        "location": data['location']
                    },
                    "time": data['time_stamp'],
                    "fields": {
                        "value": float(data['value'])
                    }
                }
            ]
            self.client.write_points(json_body, time_precision='s')
        except Exception as e:
            print(f"Error processing message: {e}")

if __name__ == "__main__":
    test = MySubscriber('VirtualBuilding')
    test.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping subscriber...")
        test.stop()
