from app.model.data_model import MachineData, UnsyncedMachineData
import logging, time, json, schedule
from configure import GeneralConfig
# from sqlalchemy import and_
from utils.threadpool import ThreadPool
import asyncio


from rabbit_mq.rabbit_client import RabbitMQPublisher
from mqtt.mqtt_client import MQTTClient
from machine.delta_sa2 import DELTA_SA2_Modbus, RedisMonitor
from flask_sqlalchemy import SQLAlchemy

async def main(rabbit_publisher: RabbitMQPublisher,
               mqtt_publisher: MQTTClient,
               redis_db_client: RedisMonitor,
               sql_db_client: SQLAlchemy,
               plc_modbus:DELTA_SA2_Modbus):
    """
    Create instance of machine object and start related functions
    """
    logging.debug("Starting program ...")
    
    mqtt_publisher.connect(keep_alive=True)
    await rabbit_publisher.connect(routing_key=['oee_data'])
    
    try:
        while True:
            await synchronize_data(rabbit_publisher, 
                                   mqtt_publisher, 
                                   redis_db_client, 
                                   sql_db_client, 
                                   plc_modbus)
            await capture_store_data(redis_db_client,
                                     sql_db_client,
                                     plc_modbus)
    except KeyboardInterrupt:
        print("KeyboardInterrupt received. Closing the publisher...")
    except Exception as e:
        logging.error(e.__str__())

async def capture_store_data(redis_db_client:RedisMonitor,
                             sql_client:SQLAlchemy,
                             plc_modbus:DELTA_SA2_Modbus):
    
    for device in plc_modbus.configure["LISTDEVICE"]:
        try:
            captured_data = dict()
            current_data = plc_modbus.read_data(device, device["ID"], captured_data)
            
            redis_topic_name    = "/device/V2/" + device["ID"] + "/raw"
            latest_data = redis_db_client.get_redis_data(redis_topic_name)
            redis_db_client.compare_and_save(device["ID"], 
                                            latest_data, 
                                            current_data, 
                                            sql_client)
        except Exception as e:
            logging.error(e.__str__())


async def synchronize_data(rabbit_publisher:RabbitMQPublisher,
                           mqtt_publisher:MQTTClient, 
                           redis_db_client:RedisMonitor,
                           sql_client:SQLAlchemy,
                           plc_modbus:DELTA_SA2_Modbus):
    
    logging.warn("synchronize_data()")
    data_tobe_sent = None
    try:

        result = sql_client.session.query(UnsyncedMachineData).order_by(UnsyncedMachineData.id.desc()).first()
        sql_client.session.close()
        data_tobe_sent = {
            "deviceId"        : result.deviceId,
            "machineStatus"   : result.machineStatus,
            "actual"          : result.actual,
            "runningNumber"   : result.runningNumber,
            "timestamp"       : result.timestamp,
            "isChanging"      : result.isChanging
        }
    except Exception as e:
        logging.error(e)
        data_tobe_sent = None
    
    if data_tobe_sent:
        logging.debug("Data need to be sent:")
        logging.debug(data_tobe_sent)
        try:
            mqtt_publisher.publish(topic= "stat/V3/" + data_tobe_sent["deviceId"] +"/OEEDATA",
                                    data=json.dumps(data_tobe_sent),
                                    qos=1,
                                    retain=True)
            
            
            logging.debug("Sending data to rabbitMQ")
            rabbit_publisher.send_message(json.dumps(data_tobe_sent))

            sql_client.session.query(UnsyncedMachineData).filter_by(timestamp=result.timestamp).delete()
            sql_client.session.commit()
            sql_client.session.close()
            logging.debug("Completed!")
        except Exception as e:
            logging.error(e.__str__())
        result = None
        data_tobe_sent = None
    time.sleep(GeneralConfig.SENDINGRATE)


# def sync_humidity_temperature(configure, redisClient, mqttClient):
#     """
#     Send humidity and temperature
#     """
#     for device in configure["LISTDEVICE"]:
#         data        = redisClient.hgetall("/device/V2/" + device["ID"] + "/raw")
#         mqttTopic   = "stat/V3/" + device["ID"]+"/HUMTEMP"
#         publishData = {}
#         if "temperature" in data and "humidity" in data:
#             publishData["clientid"]     = device["ID"]
#             publishData["temperature"]  = data["temperature"]
#             publishData["humidity"]     = data["humidity"]
#             mqttClient.publish(mqttTopic,json.dumps(publishData))
#             logging.debug("Done syncing")

# def query_data(deviceId,timeFrom,timeTo):
#     """
#     Query data for request
#     """
#     data = []
#     results = MachineData.query.filter(and_(MachineData.timestamp >= timeFrom,MachineData.timestamp <= timeTo, MachineData.deviceId == deviceId)).all()
#     for result in results:
#         data.append(
#             {
#                 "deviceId"        : result.deviceId,
#                 "machineStatus"   : result.machineStatus,
#                 "actual"          : result.actual,
#                 "runningNumber"   : result.runningNumber,
#                 "timestamp"       : result.timestamp,
#                 "temperature"     : result.temperature,
#                 "humidity"        : result.humidity,
#                 "isChanging"      : result.isChanging
#             }
#         )
#     return data
