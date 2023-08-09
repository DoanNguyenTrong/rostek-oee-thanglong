from app import mqtt_client
from utils.threadpool import ThreadPool
from .mqtt_utils import check_mqtt_connection
from configure import MQTTCnf

worker = ThreadPool(5)
worker.add_task(check_mqtt_connection,mqtt_client,MQTTCnf.BROKER,MQTTCnf.PORT)