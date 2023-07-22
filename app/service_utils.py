import logging
import time
import json 
from configure import *

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
                redisData['clientid'] = device["ID"]
                logging.warning(redisData)
                mqttClient.publish(mqttTopic, json.dumps(redisData))
            time.sleep(GeneralConfig.SENDINGRATE)
