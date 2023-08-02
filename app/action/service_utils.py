from app.model.data_model import MachineData
import logging, time, json, schedule
from configure import *
from sqlalchemy import and_
from app.machine.plc_delta import DELTA_SA2
from utils.threadpool import ThreadPool
import utils.vntime as VnTimeStamps
from app import redisClient, db

workers = ThreadPool(100)

def init_objects():
    """
    Create instance of machine object and start related functions
    """
    logging.warning("Starting program")
    plcDelta = DELTA_SA2(redisClient, deltaConfigure)
    start_service(plcDelta, deltaConfigure, redisClient, mqtt_client)

def start_service(object,configure,redisClient,mqttClient):
    """
    1. Start scheduling for syncing at default sending rate and scheduling service
    2. Start instance's internal function
    3. Start microservice for sending data
    """
    workers.add_task(start_scheduling_thread)
    rate = redisClient.hgetall(RedisCnf.RATETOPIC)
    if "machine" not in rate:
        machineRate = GeneralConfig.DEFAULTRATE 
    else:
        machineRate = int(rate["machine"])
    if "quality" not in rate:
        qualityRate = GeneralConfig.DEFAULTRATE 
    else:
        qualityRate = int(rate["qualityrate"])
    if "production" not in rate:
        productionRate = GeneralConfig.DEFAULTRATE 
    else:
        productionRate = int(rate["productionrate"])
    workers.add_task(object.start)
    workers.add_task(sync_production_data,mqttClient)
    schedule.every(machineRate).seconds.do(sync_machine_data, configure, redisClient, mqttClient)
    schedule.every(qualityRate).seconds.do(sync_quality_data, configure, redisClient, mqttClient)
    schedule.every(productionRate).seconds.do(sync_production_data, configure, redisClient, mqttClient)

def start_scheduling_thread():
    """
    Thread to schedule service
    """
    while True:
        schedule.run_pending()
        time.sleep(1)

def sync_production_data(configure, redisClient, mqttClient):
    """
    Sync production data
    """
    timeNow = int(float(VnTimeStamps.now()))
    for device in configure["LISTDEVICE"]:
        data = redisClient.hgetall(device["ID"] + "/raw")
        if data:
            sendData = {
                "record_type"   : "sx",
                "input"         : data["input"]     if ["input"]    in data else 0,
                "output"        : data["output"]    if ["output"]   in data else 0,
                "machine_id"    : device["ID"],
                "timestamp_PLC" : data["timestamp"],
                "timestamp_GW"  : timeNow,
            }
            logging.warning(sendData)
            try:
                mqttClient.publish(MQTTCnf.PRODUCTIONTOPIC, json.dumps(sendData))
                logging.warning("Complete send production data")
            except:
                pass
            
def sync_quality_data(configure, redisClient, mqttClient):
    """
    Send quality data
    """
    timeNow = int(float(VnTimeStamps.now()))
    for device in configure["LISTDEVICE"]:
        data = redisClient.hgetall(device["ID"] + "/raw")
        if data:
            sendData = {
                "record_type"   : "cl",
                "w_temp"        : data["w_temp"]    if ["w_temp"]   in data else 0,
                "ph"            : data["ph"]        if ["ph"]       in data else 0,
                "t_ev"          : data["t_ev"]      if ["t_ev"]     in data else 0,
                "uv1"           : data["uv1"]       if ["uv1"]      in data else 0,
                "uv2"           : data["uv2"]       if ["uv2"]      in data else 0,
                "uv3"           : data["uv3"]       if ["uv3"]      in data else 0,
                "p_cut"         : data["p_cut"]     if ["p_cut"]    in data else 0,
                "p_conv"        : data["p_conv"]    if ["p_conv"]   in data else 0,
                "p_gun"         : data["p_gun"]     if ["p_gun"]    in data else 0,
                "machine_id"    : device["ID"],
                "timestamp_PLC" : data["timestamp"],
                "timestamp_GW"  : timeNow
            }
            logging.warning(sendData)
            try:
                mqttClient.publish(MQTTCnf.QUALITYTOPIC, json.dumps(sendData))
                logging.warning("Complete send quality data")
            except:
                pass

def sync_machine_data(configure, redisClient, mqttClient):
    """
    Send machine data
    """
    timeNow = int(float(VnTimeStamps.now()))
    for device in configure["LISTDEVICE"]:
        data = redisClient.hgetall(device["ID"] + "/raw")
        if data:
            sendData = {
                "record_type"   : "tb", 
                "status"        : data["status"]    if ["status"]   in data else 0,
                "type"          : data["type"]      if ["type"]     in data else 0,
                "machine_id"    : device["ID"],
                "timestamp_PLC" : data["timestamp"],
                "timestamp_GW"  : timeNow,
            }
            logging.warning(sendData)
            try:
                mqttClient.publish(MQTTCnf.MACHINETOPIC, json.dumps(sendData))
                logging.warning("Complete send machine data")
            except:
                pass

def query_data(deviceId,timeFrom,timeTo):
    """
    Query data for request
    """
    data = []
    results = MachineData.query.filter(and_(MachineData.timestamp >= timeFrom,MachineData.timestamp <= timeTo, MachineData.deviceId == deviceId)).all()
    for result in results:
        data.append(
            {
                "deviceId"        : result.deviceId,
                "machineStatus"   : result.machineStatus,
                "actual"          : result.actual,
                "runningNumber"   : result.runningNumber,
                "timestamp"       : result.timestamp,
                "temperature"     : result.temperature,
                "humidity"        : result.humidity,
                "isChanging"      : result.isChanging
            }
        )
    return data

from mqtt import mqtt_client
