import time, logging
from configure import *
from utils.threadpool import ThreadPool
from app import redisClient
import schedule
from app.action.service_utils import sync_machine_data, sync_quality_data, sync_production_data

workers = ThreadPool(100)

def on_disconnect(client, userdata, rc):
    logging.warning("Disconnecting reason  "  +str(rc))
    client.loop_stop()
    client.connected_flag=False

def on_connect(client, userdata, flags, rc):
    client.connected_flag       = True
    client.reconnecting_flag    = False
    logging.warning("Connected to broker MQTT")
    client.subscribe("TLP/Fre")
    
def on_message(client, userdata, message):
    data    = json.loads(str(message.payload.decode("utf-8")))
    topic   = str(message.topic)
    deviceId = str(topic.split("/")[2])
    if "/Fre" in topic:
        logging.critical("PLPLPLPLPLPLPLP")
        handle_rate_data(client,payload,redisClient)
    
def connect(client,broker,port):
    try:
        logging.warning(f"Connecting to broker MQTT: {broker}")
        client.on_message=on_message
        client.on_connect=on_connect 
        client.on_disconnect=on_disconnect
        client.connect(broker, port ,MQTTCnf.MQTT_KEEPALIVE)
        client.username_pw_set(username=MQTTCnf.MQTT_USERNAME, password=MQTTCnf.MQTT_PASSWORD)
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

def handle_rate_data(client,data,redisClient):
    """
    Handle refresh data rate
    """
    activeScheduling = False
    schedule.clear()
    recordType = data["record_type"]
    if recordType == "sx":
        redisClient.hset(RedisCnf.RATETOPIC, "production", data["frequency"])

    elif recordType == "cl":
        redisClient.hset(RedisCnf.RATETOPIC, "quality", data["frequency"])

    elif recordType == "tb":
        redisClient.hset(RedisCnf.RATETOPIC, "machine", data["frequency"])

    activeScheduling = True
    start_sync_service()
    logging.critical(f"Scheduled every {data['frequency']} secs for {recordType} !")

def handle_request_data(deviceId,data,client):
    """
    Handle data request from server
    """
    timeFrom    = data["from"]
    timeTo      = data["to"]
    data = query_data(str(deviceId, timeFrom, timeTo))
    client.publish(json.dumps(data))

def start_scheduling_thread():
    """
    Thread to schedule service
    """
    while activeScheduling:
        schedule.run_pending()
        time.sleep(1)

def start_sync_service():
    """
    Start scheduling for syncing at default sending rate and scheduling service
    """
    rate = redisClient.hgetall(RedisCnf.RATETOPIC)
    if "machine" not in rate:
        machineRate = GeneralConfig.DEFAULTRATE 
    else:
        machineRate = int(rate["machine"])
    if "quality" not in rate:
        qualityRate = GeneralConfig.DEFAULTRATE 
    else:
        qualityRate = int(rate["quality"])
    if "production" not in rate:
        productionRate = GeneralConfig.DEFAULTRATE 
    else:
        productionRate = int(rate["production"])

    schedule.every(machineRate).seconds.do(sync_machine_data)
    schedule.every(qualityRate).seconds.do(sync_quality_data)
    schedule.every(productionRate).seconds.do(sync_production_data)
    workers.add_task(start_scheduling_thread)

activeScheduling = True
start_sync_service()
        

