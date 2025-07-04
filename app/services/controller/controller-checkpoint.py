# services/controller/controller.py

from virtual_devices import simpleSubscriber as sub
from virtual_devices import simplePublisher as pub
import json
import time
import os  # Aggiunto per accedere alle variabili d'ambiente

class MyController():
    def __init__(self, clientID, topic):
        # Recupera l'host del broker MQTT dalle variabili d'ambiente
        mqtt_broker = os.getenv('MQTT_BROKER_HOST', 'mosquitto')  # Default a 'mosquitto' se non specificato
        mqtt_port = int(os.getenv('MQTT_BROKER_PORT', 1883))     # Recupera la porta MQTT, default 1883

        # Crea un'istanza di MySubscriber e MyPublisher con l'host corretto
        self.clientID = clientID
        self.topic = topic
        self.myMqttClient_sub = sub.MySubscriber(
            self.clientID,
            topic=self.topic,
            broker=mqtt_broker,   # Utilizza l'host dal ambiente
            port=mqtt_port,       # Utilizza la porta dal ambiente
            notifier=self
        )
        self.myMqttClient_pub = pub.MyPublisher(
            self.clientID + '1'
        )
        self.set_Globals()
        
    def run(self):
        # Se necessario, esegui altre azioni prima di avviare la comunicazione MQTT
        print(f"Running {self.clientID}")
        self.myMqttClient_sub.start() 
        
        self.myMqttClient_pub.start()
        print(f"Started {self.clientID}")

    def end(self):
        # Se necessario, esegui altre azioni prima di terminare il software
        print(f"Ending {self.clientID}")
        self.myMqttClient_sub.stop()
        self.myMqttClient_pub.stop()

    def notify(self, msg):
        # Gestisci qui il messaggio ricevuto. Puoi eseguire controlli di errore.
        print(f"Received message: {msg.payload}")
        try:
            self.msg = json.loads(msg.payload)
            self.T_ext = float(self.msg.get('T_ext', 0))
            self.Rad = float(self.msg.get('DNI', 0))
            self.Tin_Bathroom1 = float(self.msg.get('Tin_Bathroom1', 0))
            self.Tin_Room1 = float(self.msg.get('Tin_Room1', 0))
            self.Tin_Bathroom = float(self.msg.get('Tin_Bathroom', 0))
            self.Tin_Livingroom = float(self.msg.get('Tin_Livingroom', 0))
            self.Tin_Room = float(self.msg.get('Tin_Room', 0))
            self.send_action()
        except Exception as e:
            print(f"Error processing message: {e}")

    def set_Globals(self):
        self.radTrig = 100
        self.TinTrig = 24
        self.payload = {
            'Bath1_shade': 0.0,
            'Room1_shade1': 0.0,
            'Room1_shade2': 0.0,
            'Bath_shade': 0.0,
            'Living_shade1': 0.0,
            'Living_shade2': 0.0,
            'Room_shade1': 0.0,
            'Room_shade2': 0.0
        }

    def send_action(self):
        # Logica di controllo
        if self.Tin_Bathroom1 > self.TinTrig and self.Rad > self.radTrig:
            self.payload['Bath1_shade'] = 7.0
        else:
            self.payload['Bath1_shade'] = 0.0

        if self.Tin_Bathroom > self.TinTrig and self.Rad > self.radTrig:
            self.payload['Bath_shade'] = 7.0
        else:
            self.payload['Bath_shade'] = 0.0

        if self.Tin_Room1 > self.TinTrig and self.Rad > self.radTrig:
            self.payload['Room1_shade1'] = 7.0
            self.payload['Room1_shade2'] = 7.0
        else:
            self.payload['Room1_shade1'] = 0.0
            self.payload['Room1_shade2'] = 0.0

        if self.Tin_Livingroom > self.TinTrig and self.Rad > self.radTrig:
            self.payload['Living_shade1'] = 7.0
            self.payload['Living_shade2'] = 7.0
        else:
            self.payload['Living_shade1'] = 0.0
            self.payload['Living_shade2'] = 0.0

        if self.Tin_Room > self.TinTrig and self.Rad > self.radTrig:
            self.payload['Room_shade1'] = 7.0
            self.payload['Room_shade2'] = 7.0
        else:
            self.payload['Room_shade1'] = 0.0
            self.payload['Room_shade2'] = 0.0

        # Pubblica il payload sul topic 'actuator'
        self.myMqttClient_pub.myPublish("/actuator", json.dumps(self.payload))
        print(f"Action sent: {self.payload}")

if __name__ == "__main__":
    test = MyController('VirtualBuildingController', '/all_data_controller')
    test.run()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        test.end()
