from app import mqtt, db, redisClient
from app.model.data_model import MachineData
from app.action.service_utils import *
import logging, json
from configure import GeneralConfig, RedisCnf
from utils.threadpool import ThreadPool
import schedule, socket
workers = ThreadPool(10)
@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    logging.warning("ON CONNECT")
    
@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
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

def handle_request_data(data,client):
    """
    Handle data request from server
    """
    deviceId    = data["machine_id"]
    timeFrom    = data["time_start"]
    timeTo      = data["time_end"]
    data = query_data(str(deviceId, timeFrom, timeTo))
    client.publish(json.dumps(data))

def query_data(deviceId,timeFrom,timeTo):
    """
    Query data for request
    """
    data = []
    results = MachineData.query.filter(and_(MachineData.timestamp >= timeFrom,MachineData.timestamp <= timeTo, MachineData.deviceId == deviceId)).all()
    if results:
        for result in results:
            data.append(
                {
                    "deviceId"          : result.deviceId,
                    "machineStatus"     : result.machineStatus,
                    "output"            : result.output,
                    "input"             : result.input,
                    "envTemp"           : result.envTemp,
                    "envHum"            : result.envHum,
                    "waterTemp"         : result.waterTemp,
                    "waterpH"           : result.waterpH,
                    "timestamp"         : result.timestamp,
                    "uv1"               : result.uv1,
                    "uv2"               : result.uv2,
                    "uv3"               : result.uv3,
                    "upperAirPressure"  : result.upperAirPressure,
                    "lowerAirPressure"  : result.lowerAirPressure,
                    "gluePressure"      : result.gluePressure,
                    "glueTemp"          : result.glueTemp
                }
            )
        return data
    else:
        return -1

def cmd_handler(payload):
    try:
        mqtt.publish("/gateway/reply", json.dumps({
            "local_ip" : get_ip()
        }))
    except Exception as e:
        logging.error(str(e))

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 5))
    ipv4 = s.getsockname()[0]
    s.close()
    return ipv4
                
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
    # logging.error(f"Scheduled every {data['frequency']} secs for {recordType} !")

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