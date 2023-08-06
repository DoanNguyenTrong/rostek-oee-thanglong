import logging, time
import paho.mqtt.client as mqtt
import json

from configure import SharedMemCfg, MQTTCnf

import numpy as np
from multiprocessing import shared_memory

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class MQTTClient():
    __instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance
    
    def __init__(self, configures:MQTTCnf, user_data:dict):
        self.configures = configures
        self.user_data = user_data

        self.keepalive = False

        self.client = mqtt.Client(self.configures.BROKER_IP, 
                                  userdata=user_data, 
                                  clean_session=False, 
                                  reconnect_on_failure=True)
        
        self.client.username_pw_set(username=self.configures.MQTT_USERNAME,
                                    password=self.configures.MQTT_PASSWORD)
        
        self.subscribe_topic = []  # Store the topic for re-subscription

        #self.client.on_log        = on_log
        
        # # username and password
        # if not credential == None:
        #     logging.info( "Login a network with credential verification" )
        #     try:
        #         self.client.username_pw_set(username=credential[0],password=credential[1])
        #     except Exception as e:
        #         logging.error(e.__str__())
        #         logging.error(f"Credential: {credential}")
    
    def connect(self, keep_alive=True, sleeptime=2):
        """Connect to broker:port"""
        logging.info("Connecting to broker {}:{}".format(self.configures.BROKER_IP,
                                                         self.configures.PORT))
        try:
            self.client.connect(self.configures.BROKER_IP, 
                                port=self.configures.PORT, 
                                keepalive=keep_alive) #connect to broker
            
            self.keepalive = keep_alive
            
            # callback functions
            self.client.on_publish = self.on_publish
            self.client.on_message = self.on_message
            self.client.on_subscribe = self.on_subscribe
            self.client.on_disconnect = self.on_disconnect
            self.client.on_log = self.on_log

            self.client.loop_start()
            time.sleep(sleeptime) # Wait for connection setup to complete
        except Exception as e:
            logging.error(e.__str__())
    

    def publish(self, topic, data, qos = 1, retain=False):
        """Publish "data" -> "topic" """

        logging.debug("Publishing message to topic %s" % topic)
        self.user_data['topic'] = topic
        self.client.user_data_set(self.user_data)
        result, mid = self.client.publish(topic, data, qos=qos, retain=retain)
        if result != 0:
            logging.error(f'Failed to send, rc: {result}')
    
    
    def disconnect(self):
        logging.debug("Disconnecting...........")
        self.client.loop_stop()
        self.client.disconnect()

    
    def on_connect(self, client, flags, rc):
        """Callback function when a connection is establised"""
        if rc==0:
            self.client.connected_flag=True #set flag
            self.client.reconnecting_flag    = False # TODO: unknown
            logging.info("Connected OK Returned code: %s \n"%rc)
            logging.critical(f'Subscribing to topic /TLP/Fre')
            self.client.subscribe("/TLP/Fre")
        else:
            logging.info("Bad connection Returned code: %s \n"%rc)

    def on_subscribe(self, client, userdata, mid, granted_qos):
        logging.critical(f"Subscribed to topic with MID:{mid}, {granted_qos}")

    def on_disconnect(self, client, userdata, rc):
        """Callback function when disconnection"""

        logging.error("Disconnecting reason %s " % str(rc))
        self.client.connected_flag=False
        self.client.disconnect_flag=True

    def on_message(self, client, userdata, message):
        """
            Callback function when client is a CO2 publisher
            print out the received message
            check FLAG and perform mode switching
        """
        received_data    = json.loads(str(message.payload.decode("utf-8")))
        message_topic   = str(message.topic)
        deviceId = str(message_topic.split("/")[2]) 

        topic   = str(message.topic)
        deviceId = str(topic.split("/")[2])
        logging.critical("Topic: {}, msg: {}, retained: {}".format(message_topic, \
                                                            message.payload.decode("utf-8"), \
                                                            message.retain))
        if "/TLP/Fre" in topic:
            existing_shm = shared_memory.SharedMemory(name=SharedMemCfg.MEM_NAME)
            recordType = received_data["record_type"]
            logging.debug(f"Receive control command to topic:{topic}, data: {received_data}")
            if recordType == "sx":
                freq = int(received_data["frequency"])
                logging.critical(f"Change production publish freq to {freq}")
                existing_shm.buf[SharedMemCfg.MEM_SX_IDX] = freq
            elif recordType == "cl":
                freq = int(received_data["frequency"])
                logging.critical(f"Change quality publish freq to {freq}")
                existing_shm.buf[SharedMemCfg.MEM_CL_IDX] = freq
            elif recordType == "tb":
                freq = int(received_data["frequency"])
                logging.critical(f"Change machine publish freq to {freq}")
                existing_shm.buf[SharedMemCfg.MEM_TB_IDX] = freq
        
        if message.retain==1:
            logging.debug("This is a retained message")

    def on_publish(self, client,userdata,result):
        """Callback if a message is publised"""
        logging.debug(f"Message published with result:{result}")
        logging.debug(f"data published to {userdata['topic']}\n")

    def on_log(self, client, userdata, level, buf):
        """
        Troubleshoot using Logging
        """
        logging.info(f"MQTTClient log: {buf}")

def mqtt_subscriber():
   
    # Create an MQTT client
    client = MQTTClient(configures=MQTTCnf, user_data={})
    

    # Connect to the broker
    client.connect(keep_alive=True)

    # client.client.loop_start()

    try:
        while True:
            time.sleep(0.5)  # Keep the script running
    except KeyboardInterrupt:
        pass  # Stop the script gracefully

    # Disconnect from the broker
    client.client.loop_stop()
    client.client.disconnect()


if __name__ == "__main__":
    mqtt_subscriber()