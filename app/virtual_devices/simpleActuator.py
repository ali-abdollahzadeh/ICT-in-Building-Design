from . import simpleSubscriber as sub

class MyActuator():
	def __init__(self, clientID,topic):
		# create an instance of MyMQTT class
		self.clientID = clientID
		self.topic=topic
		self.myMqttClient = sub.MySubscriber(self.clientID, topic=self.topic,broker="mosquitto", port=1883, notifier=self)
		self.wait=True
		


	def run(self):
		# if needed, perform some other actions befor starting the mqtt communication
		print ("running %s" % (self.clientID))
		self.myMqttClient.start()

	def end(self):
		# if needed, perform some other actions befor ending the software
		print ("ending %s" % (self.clientID))
		self.myMqttClient.stop ()

	def notify(self,msg):
		# manage here your received message. You can perform some error-check here
		self.msg=msg
		self.wait=False
		print ("received '%s' under topic '%s'" % (msg.payload, msg.topic))




