import paho.mqtt.client as mqtt 
from utils.threadpool import ThreadPool
from .mqtt_utils import check_mqtt_connection
from configure import MQTTCnf

mqtt.Client.connected_flag      = False
mqtt.Client.reconnecting_flag   = False

mqtt_client = mqtt.Client()           

worker = ThreadPool(5)
worker.add_task(check_mqtt_connection,mqtt_client,MQTTCnf.BROKER,MQTTCnf.PORT)