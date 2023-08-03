from app.model.data_model import MachineData
from app.model.unsynced_data import UnsyncedMachineData
import logging, time, json, schedule
from configure import *
from sqlalchemy import and_
from app.machine.plc_delta import DELTA_SA2
from utils.threadpool import ThreadPool
from app import redisClient
from rabbit_mq import RabbitMQ
import asyncio

workers = ThreadPool(100)

# async def main(rabbit_publisher:RabbitMQ):
#     """
#     Create instance of machine object and start related functions
#     """
#     logging.warning("Starting program")
#     tasks = []
#     plcDelta = DELTA_SA2(redisClient, deltaConfigure)
#     # asyncio.run(start_services(tasks, plcDelta, deltaConfigure, redisClient, mqtt_client, rabbit_publisher))
    
#     humTempRate = redisClient.hgetall(RedisCnf.HUMTEMPTOPIC)
#     if "humtemprate" not in humTempRate:
#         humTempRate = GeneralConfig.DEFAULTRATE 
#     else:
#         humTempRate = int(humTempRate["humtemprate"])
    
#     loop = asyncio.get_event_loop()
#     tasks.append(loop.create_task(plcDelta.start))
#     await asyncio.sleep(0)
#     tasks.append( loop.create_task(synchronize_data,mqtt_client, rabbit_publisher) )
#     await asyncio.sleep(0)
#     tasks.append( loop.create_task(hum_loop,deltaConfigure, redisClient, mqtt_client, humTempRate) )
#     await asyncio.sleep(0)
    
#     # Run the event loop indefinitely until the task is done
#     try:
#         loop.run_forever()
#     except KeyboardInterrupt:
#         pass
#     finally:
#         loop.close()

async def main(rabbit_publisher: RabbitMQ):
    """
    Create instance of machine object and start related functions
    """
    logging.warning("Starting program")
    tasks = []
    plcDelta = DELTA_SA2(redisClient, deltaConfigure)

    humTempRate = redisClient.hgetall(RedisCnf.HUMTEMPTOPIC)
    if "humtemprate" not in humTempRate:
        humTempRate = GeneralConfig.DEFAULTRATE
    else:
        humTempRate = int(humTempRate["humtemprate"])

    loop = asyncio.get_event_loop()
    tasks.append(loop.create_task(plcDelta.start()))  # Call plcDelta.start as a coroutine
    tasks.append(loop.create_task(synchronize_data(mqtt_client, rabbit_publisher)))  # Call synchronize_data as a coroutine
    tasks.append(loop.create_task(hum_loop(deltaConfigure, redisClient, mqtt_client, humTempRate)))  # Call hum_loop as a coroutine
    
    # Run the event loop until all tasks are done
    try:
        for task in tasks:
            await asyncio.gather(*task)
    except KeyboardInterrupt:
        pass


async def hum_loop(configure, redisClient, mqttClient, sleeptime:int=1):
    """
    Thread to schedule service
    """
    while True:
        logging.warn("hum_loop()")
        sync_humidity_temperature(configure, redisClient, mqttClient)
        time.sleep(sleeptime)

async def synchronize_data(mqttClient, rabbit_publisher:RabbitMQ):
    """
    Go to database named UnsyncedMachineData, get data and publish by MQTT to server 
    """
    while True:
        logging.warn("synchronize_data()")
        sendData = None
        # a =  db.session.query(UnsyncedMachineData).all()
        # db.session.close()
        # for i in a:
        #     logging.error(i.id)
        try:
            # result = UnsyncedMachineData.query.order_by(UnsyncedMachineData.id.desc()).first()
            result = db.session.query(UnsyncedMachineData).order_by(UnsyncedMachineData.id.desc()).first()
            db.session.close()
            sendData = {
                "deviceId"        : result.deviceId,
                "machineStatus"   : result.machineStatus,
                "actual"          : result.actual,
                "runningNumber"   : result.runningNumber,
                "timestamp"       : result.timestamp,
                "isChanging"      : result.isChanging
            }
        except Exception as e:
            logging.error(e)
            sendData = None
        
        if sendData:
            logging.warning(sendData)
            try:
                mqttClient.publish("stat/V3/" + result.deviceId +"/OEEDATA",json.dumps(sendData))
                
                logging.warning("Sending data to rabbitMQ")
                asyncio.run( rabbit_publisher.send_message(json.dumps(sendData)) )
                
                # logging.error("stat/V3/" + result.deviceId +"/OEEDATA")
                db.session.query(UnsyncedMachineData).filter_by(timestamp=result.timestamp).delete()
                db.session.commit()
                db.session.close()
                logging.warning("Complete sending")
            except Exception as e:
                logging.error(e.__str__())
            result = None
            sendData = None
        time.sleep(GeneralConfig.SENDINGRATE)

def sync_humidity_temperature(configure, redisClient, mqttClient):
    """
    Send humidity and temperature
    """
    for device in configure["LISTDEVICE"]:
        data        = redisClient.hgetall("/device/V2/" + device["ID"] + "/raw")
        mqttTopic   = "stat/V3/" + device["ID"]+"/HUMTEMP"
        publishData = {}
        if "temperature" in data and "humidity" in data:
            publishData["clientid"]     = device["ID"]
            publishData["temperature"]  = data["temperature"]
            publishData["humidity"]     = data["humidity"]
            mqttClient.publish(mqttTopic,json.dumps(publishData))
            logging.debug("Done syncing")

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
