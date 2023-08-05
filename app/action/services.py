import logging
import time
import json
import asyncio

import app.mqtt_client as mqtt_client
import configure 
import rabbit_mq.rabbit_client as rabbit_client
import app.machine.delta_sa2 as devices
from flask_sqlalchemy import SQLAlchemy

from app import db_client

async def rostek_oee(rabbit_publisher: rabbit_client.RabbitMQPublisher,
               mqtt_publisher: mqtt_client.MQTTClient,
               redis_client):
    """
    Create instance of machine object and start related functions
    """
    logging.debug("Starting program ...")
    
    mqtt_publisher.connect(keep_alive=True)
    await rabbit_publisher.connect(routing_key=['oee_data'])
    
    # hardware device
    plc_modbus  = devices.DELTA_SA2_Modbus(configure.deltaConfigure)
    redis_db_client = devices.RedisMonitor(redis_client=redis_client,
                                sql_database_client=db_client,
                                configure=configure.RedisCnf)

    try:
        while True:
            publish_task = synchronize_data(rabbit_publisher, 
                                   mqtt_publisher, 
                                   redis_db_client, 
                                   db_client, 
                                   plc_modbus)
            monitor_task = capture_store_data(redis_db_client,
                                     db_client,
                                     plc_modbus)
            await asyncio.gather(publish_task, monitor_task)

    except KeyboardInterrupt:
        print("KeyboardInterrupt received. Closing the publisher...")
    except Exception as e:
        logging.error(e.__str__())

async def capture_store_data(redis_db_client:devices.RedisMonitor,
                             sql_client:SQLAlchemy,
                             plc_modbus:devices.DELTA_SA2_Modbus):
    
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


async def synchronize_data(rabbit_publisher:rabbit_client.RabbitMQPublisher,
                           mqtt_publisher:mqtt_client.MQTTClient, 
                           redis_db_client:devices.RedisMonitor,
                           sql_client:SQLAlchemy,
                           plc_modbus:devices.DELTA_SA2_Modbus):
    
    logging.debug("Execute synchronize_data()")
    data_tobe_sent = None
    try:

        result = sql_client.session.query(devices.UnsyncedMachineData).order_by(devices.UnsyncedMachineData.id.desc()).first()
        sql_client.session.close()
        logging.warning(f'Result: {result}')
        if result is not None:
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
    
    if data_tobe_sent is not None:
        logging.debug("Data need to be sent:")
        logging.debug(data_tobe_sent)
        try:
            mqtt_publisher.publish(topic= "stat/V3/" + data_tobe_sent["deviceId"] +"/OEEDATA",
                                    data=json.dumps(data_tobe_sent),
                                    qos=1,
                                    retain=True)
            
            
            logging.debug("Sending data to rabbitMQ")
            rabbit_publisher.send_message(json.dumps(data_tobe_sent))

            sql_client.session.query(devices.UnsyncedMachineData).filter_by(timestamp=result.timestamp).delete()
            sql_client.session.commit()
            sql_client.session.close()
            logging.debug("Completed!")
        except Exception as e:
            logging.error(e.__str__())
        result = None
        data_tobe_sent = None
    else:
        logging.debug("Data queue is empty!")
    # time.sleep(configure.GeneralConfig.SENDINGRATE)

