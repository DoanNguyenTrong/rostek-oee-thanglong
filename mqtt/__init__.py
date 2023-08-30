import paho.mqtt.client as mqtt 
from utils.threadpool import ThreadPool
from configure import MQTTCnf
import logging
import time, json
from app.action.service_utils import *

class MqttService:
    __instance = None
    @staticmethod
    def get_instance():
        if MqttService.__instance == None:
            MqttService()
        return MqttService.__instance

    def __init__(self):
        if MqttService.__instance != None:
            raise Exception("Do not call __init__().")
        else:
            MqttService.__instance  = self
            self.client             = mqtt.Client()       
            self.connected_flag     = False
            self.reconnecting_flag  = False
            self.worker             = ThreadPool(10)
            self.broker             = MQTTCnf.BROKER
            self.port               = MQTTCnf.PORT
            self.username           = MQTTCnf.MQTT_USERNAME
            self.password           = MQTTCnf.MQTT_PASSWORD
            self.keepalive          = MQTTCnf.MQTT_KEEPALIVE
            self.worker.add_task(self.check_mqtt_connection)

    def connect(self):
        try:
            logging.warning(f"Connecting to broker MQTT: {self.broker}")
            self.client.on_message=self.on_message
            self.client.on_connect=self.on_connect 
            self.client.on_disconnect=self.on_disconnect
            self.client.username_pw_set(username=self.username, password=self.password)
            self.client.connect(self.broker, self.port, self.keepalive)
            self.client.loop_forever()
            # self.client.loop_start()
            
        except:
            logging.error("MQTT connection failed")
            self.reconnect()

    def check_mqtt_connection(self):
        """
        Check if MQTT connected, auto reconnect if disconnect
        """
        while True:
            logging.critical(self.connected_flag)
            if not self.connected_flag and not self.reconnecting_flag:
                self.connect()
            time.sleep(5)

    def on_message(self, client, userdata, message):
        topic=message.topic
        try:
            payload=json.loads(message.payload.decode())
            logging.error("Messsssssssage")
            # logging.error(f"{topic} -- {payload}")
            if "/Fre" in topic:
                handle_rate_data(client,payload,redisClient)
            elif "/cmd" in topic:
                cmd_handler(payload)
            elif "/Recall" in topic:
                handle_request_data(payload, client)
        except:
            logging.critical(message.payload.decode())

    

    def on_disconnect(self, client, userdata, rc):
        logging.warning("Disconnecting reason  "  +str(rc))
        client.loop_stop()
        client.connected_flag=False

    def on_connect(self, client, userdata, flags, rc):
        client.connected_flag       = True
        client.reconnecting_flag    = False
        logging.warning("Connected to broker MQTT")
        client.subscribe(MQTTCnf.RATETOPIC)
        client.subscribe(MQTTCnf.RECALLTOPIC)
        client.subscribe("/rostek/cmd")
        
    def reconnect(self):
        logging.warning("Trying to reconnect MQTT")
        time.sleep(5)
        self.connect()
        self.reconnecting_flag = True

