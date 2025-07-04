import paho.mqtt.client as PahoMQTT
import time
import json
import os
from influxdb import InfluxDBClient

class MySubscriber:
		def __init__(self, clientID, topic=None,broker="mosquitto", port = 1883, notifier=None):
			self.clientID = clientID
			self.notifier=notifier
			self.port = port
			# create an instance of paho.mqtt.client
			self._paho_mqtt = PahoMQTT.Client(clientID, False) 

			# register the callback
			self._paho_mqtt.on_connect = self.myOnConnect
			self._paho_mqtt.on_message = self.myOnMessageReceived
			print(topic)
			if topic == None:
				self.topic = 'ict4bd'
			else:
				self.topic=topic
			self.messageBroker = "mosquitto"
			influxdb_host = os.environ.get('INFLUXDB_HOST', 'influxdb')
			self.client = InfluxDBClient(influxdb_host, 8086, 'root', 'root', clientID)
			if {'name': clientID} not in self.client.get_list_database():
					self.client.create_database(clientID)


		def start (self):
			#manage connection to broker
			self._paho_mqtt.connect(self.messageBroker, self.port)
			self._paho_mqtt.loop_start()
			# subscribe for a topic
			self._paho_mqtt.subscribe(self.topic, 2)

		def stop (self):
			self._paho_mqtt.unsubscribe(self.topic)
			self._paho_mqtt.loop_stop()
			self._paho_mqtt.disconnect()

		def myOnConnect (self, paho_mqtt, userdata, flags, rc):
			print ("Sub Connected to %s with result code: %d" % (self.messageBroker, rc))

		def myOnMessageReceived (self, paho_mqtt , userdata, msg):
			# A new message is received
			#print ("Topic:'" + msg.topic+"', QoS: '"+str(msg.qos)+"' Message: '"+str(msg.payload) + "'")
			if self.notifier is not None:
				#self.notifier.wait=False
				self.notifier.notify(msg)


if __name__ == "__main__":
	test = MySubscriber('VirtualBuilding')
	test.start()
	while (True):
		pass