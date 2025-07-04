import os
import paho.mqtt.client as PahoMQTT
import time
import pandas as pd
import json

class MyPublisher:
    def __init__(self, clientID):
        self.clientID = clientID
        # Create an instance of paho.mqtt.client
        self._paho_mqtt = PahoMQTT.Client(client_id=self.clientID)
        # Register the callback
        self._paho_mqtt.on_connect = self.myOnConnect
        # Use environment variable for message broker host
        self.messageBroker = "mosquitto"

    def start(self):
        try:
            # Manage connection to broker
            self._paho_mqtt.connect(self.messageBroker, 1883)
            self._paho_mqtt.loop_start()
        except Exception as e:
            print(f"Error connecting to MQTT broker at {self.messageBroker}: {e}")
            self.stop()

    def stop(self):
        self._paho_mqtt.loop_stop()
        self._paho_mqtt.disconnect()

    def myPublish(self, topic, message):
        # Publish a message with a certain topic
        self._paho_mqtt.publish(topic, message, 2)

    def myOnConnect(self, paho_mqtt, userdata, flags, rc):
        print(f"Connected to {self.messageBroker} with result code: {rc}")

if __name__ == "__main__":
    test = MyPublisher("MyPublisher")
    test.start()
    df = pd.read_csv('data.csv', sep=',', decimal=',', index_col=0)
    df.index = pd.to_datetime(df.index, unit='s')
    GATEWAY_NAME = "VirtualBuilding"
    for i in df.index:
        print(i,df.index[-1]) 
        for nodeID, value in df.loc[i].items():
            measurement = "Power" if nodeID == 'Power' else "Temperature"
            payload = {
                "location": GATEWAY_NAME,
                "measurement": measurement,
                "node": nodeID,
                "time_stamp": str(i),
                "value": value
            }
            test.myPublish('ict4bd', json.dumps(payload))
    test.stop()