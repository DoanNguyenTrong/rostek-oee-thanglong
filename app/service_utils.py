import logging, time, json
from configure import *
import schedule
from .model.data_model import MachineData
from .model.unsynced_data import UnsyncedMachineData
from sqlalchemy.orm import Session
from sqlalchemy import and_

def synchronize_data(configure, redisClient, mqttClient, engine):
    """
    Go to redis, get data and publish by MQTT to server 
    """
    while True:
        for device in configure["LISTDEVICE"]:
            redisTopic  =  device["ID"] + "/event"
            mqttTopic   = "stat/V2/" + device["ID"]+"/OEEDATA"
            sendData   = None
            try:
                session = Session(engine)
                result = session.query(UnsyncedMachineData).order_by(UnsyncedMachineData.id.desc()).first()
                logging.error(result)
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
                logging.error(e)
                sendData = None
            if sendData:
                logging.warning(sendData)
                session = Session(engine)
                logging.error(result.id)
                session.query(UnsyncedMachineData).filter_by(id=result.id).delete()
                logging.error("Complete sending")
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
    session = Session(engine)
    results = session.query(MachineData).filter(and_(MachineData.timestamp >= timeFrom,MachineData.timestamp <= timeTo, MachineData.deviceId == deviceId)).all()
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