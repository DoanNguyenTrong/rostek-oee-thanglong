from app.model.data_model import MachineData
from app.model.unsynced_data import UnsyncedMachineData
import logging, time, json, schedule
from configure import *
from sqlalchemy import and_
from mqtt import mqtt_client
from app.machine.plc_delta import DELTA_SA2
from utils.threadpool import ThreadPool
from app import redisClient

workers = ThreadPool(100)
def start_scheduling_thread():
    while True:
        schedule.run_pending()
        time.sleep(1)

def start_service(object,configure,redisClient,mqttClient):
    humTempRate = redisClient.hgetall(RedisCnf.HUMTEMPTOPIC)
    if "humtemprate" not in humTempRate:
        humTempRate = GeneralConfig.DEFAULTRATE 
    else:
        humTempRate = int(humTempRate)
    workers.add_task(object.start)
    # workers.add_task(synchronize_data, configure, redisClient, mqttClient)
    # schedule.every(humTempRate).seconds.do(sync_humidity_temperature, configure, redisClient, mqttClient)

def init_objects():
    logging.warning("Starting program")
    plcDelta = DELTA_SA2(redisClient,deltaConfigure)
    start_service(plcDelta,deltaConfigure,redisClient,mqtt_client)

def synchronize_data(configure, redisClient, mqttClient):
    """
    Go to redis, get data and publish by MQTT to server 
    """
    while True:
        for device in configure["LISTDEVICE"]:
            redisTopic  =  device["ID"] + "/event"
            mqttTopic   = "stat/V2/" + device["ID"]+"/OEEDATA"
            sendData   = None
            try:
                # session = Session()
                result = UnsyncedMachineData.query().order_by(UnsyncedMachineData.id.desc()).first()
                sendData = {
                    "deviceId"        : result.deviceId,
                    "machineStatus"   : result.machineStatus,
                    "actual"          : result.actual,
                    "runningNumber"   : result.runningNumber,
                    "timestamp"       : result.timestamp,
                    "temperature"     : result.temperature,
                    "humidity"        : result.humidity
                }
            except Exception as e:
                # logging.error(e)
                sendData = None
            if sendData:
                UnsyncedMachineData.query().filter_by(timestamp=result.timestamp).delete()
                logging.error("Complete sending")
                result = None
            time.sleep(GeneralConfig.SENDINGRATE)

def sync_humidity_temperature(configure, redisClient, mqttClient):
    for device in configure["LISTDEVICE"]:
        data        = redisClient.hgetall("/device/V2/" + device["ID"] + "/raw")
        mqttTopic   = "stat/V2/" + device["ID"]+"/HUMTEMP"
        publishData = {}
        if "temperature" in data and "humidity" in data:
            publishData["clientid"]     = device["ID"]
            publishData["temperature"]  = device["temperature"]
            publishData["humidity"]     = device["humidity"]
            mqttClient.publish(mqttTopic,json.dumps(publishData))

def query_data(deviceId,timeFrom,timeTo):
    data = []
    results = MachineData.query().filter(and_(MachineData.timestamp >= timeFrom,MachineData.timestamp <= timeTo, MachineData.deviceId == deviceId)).all()
    for result in results:
        data.append(
            {
                "deviceId"        : result.deviceId,
                "machineStatus"   : result.machineStatus,
                "actual"          : result.actual,
                "runningNumber"   : result.runningNumber,
                "timestamp"       : result.timestamp,
                "temperature"     : result.temperature,
                "humidity"        : result.humidity
            }
        )
    return data

workers.add_task(start_scheduling_thread)