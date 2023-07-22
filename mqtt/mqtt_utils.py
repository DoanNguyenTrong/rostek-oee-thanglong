import time
import logging
from configure import *
from utils.threadpool import ThreadPool
from .handle_message import *
from app import redisClient
workers = ThreadPool(100)

def on_disconnect(client, userdata, rc):
    logging.warning("Disconnecting reason  "  +str(rc))
    client.loop_stop()
    client.connected_flag=False

def on_connect(client, userdata, flags, rc):
    client.connected_flag       = True
    client.reconnecting_flag    = False
    logging.warning("Connected to broker MQTT")
    client.subscribe("cmnd/V2/+/OEEWorkingShift")
    client.subscribe("cmnd/V2/+/OEECHANGEPRODUCT")
    
def on_message(client, userdata, message):
    data    = json.loads(str(message.payload.decode("utf-8")))
    topic   = str(message.topic)
    deviceId = str(topic.split("/")[2])
    if "/OEEWorkingShift" in topic:
        workers.add_task(handle_shift_data,deviceId,data,redisClient)
    elif "/OEECHANGEPRODUCT" in topic:
        workers.add_task(handle_production_data,deviceId,data,redisClient)
    #     print(deviceId)
    # print(topic)
    # print(data)
    
def connect(client,broker,port):
    try:
        logging.info(f"Connecting to broker MQTT: {broker}")
        client.on_message=on_message
        client.on_connect=on_connect 
        client.on_disconnect=on_disconnect
        client.connect(broker, port ,MQTTCnf.MQTT_KEEPALIVE)
        client.username_pw_set(username=MQTTCnf.MQTT_USERNAME, password=MQTTCnf.MQTT_PASSWORD)

        # client.on_message = on_message
        # client.loop_start()
        client.connected_flag = True
        client.loop_forever()
        
    except:
        logging.error("MQTT connection failed")
        reconnect(client,broker,port)

def reconnect(client,broker,port):
    logging.warning("Trying to reconnect MQTT")
    time.sleep(5)
    connect(client,broker,port)
    client.reconnecting_flag = True

def check_mqtt_connection(client,broker,port):
    """
    Check if MQTT connected, auto reconnect if disconnect
    """
    while True:
        logging.debug(client.connected_flag)
        if not client.connected_flag and not client.reconnecting_flag:
            # logging.warning("MQTT unconnected, trying to reconnect!")
            connect(client,broker,port)
        time.sleep(15)


        

