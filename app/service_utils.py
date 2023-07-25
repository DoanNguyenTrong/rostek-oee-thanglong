import logging
import time
import json 
from configure import *
import schedule
from .model.data_model import MachineData
from sqlalchemy.orm import Session

def synchronize_data(configure, redisClient, mqttClient):
    """
    Go to redis, get data and publish by MQTT to server 
    """
    while True:
        for device in configure["LISTDEVICE"]:
            redisTopic  =  device["ID"] + "event"
            mqttTopic   = "stat/V2/" + device["ID"]+"/OEEDATA"
            redisData   = None
            try:
                redisData = redisClient.lrange(redisTopic,0,-1)[0]
            except:
                redisData = None
            # logging.error(redisData)
            if redisData:
                redisData["clientid"] = device["ID"]
                logging.warning(redisData)
                mqttClient.publish(mqttTopic, json.dumps(redisData))
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
    stmt = select(MachineData).where(MachineData.device_id == deviceId)