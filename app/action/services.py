import logging
import time
import json
import asyncio
from flask_sqlalchemy import SQLAlchemy

import app.mqtt_client as mqtt_client
import configure 
import app.rabbit_client as rabbit_client
from app.machine.devices import UvMachine
from app.redis_client import RedisMonitor
from app.model.data_model import MachineData, UnsyncedMachineData
from app.utils import vntime as VnTimeStamps
from app import db_client


async def publish_task(mqtt_handler, publish_topic, message, publish_interval):
    while True:
        mqtt_handler.publish(publish_topic, message)
        await asyncio.sleep(publish_interval)

async def another_task():
    while True:
        logging.info("Another task is running...")
        await asyncio.sleep(10)

async def rostek_oee(rabbit_publisher: rabbit_client.RabbitMQPublisher,
               mqtt_publisher: mqtt_client.MQTTClient,
               redis_obj):
    """
    Create instance of machine object and start related functions
    """
    logging.info("Starting program ...")
    
    mqtt_publisher.connect(keep_alive=True)
    mqtt_publisher.subscribe([configure.MQTTCnf.RATETOPIC])

    await rabbit_publisher.connect(routing_key=['oee_data'])
    
    # hardware device
    plc_modbus  = UvMachine(configure.uvMachineConfigure)
    redis_db_client = RedisMonitor(redis_client=redis_obj,
                                sql_database_client=db_client,
                                configure=configure.RedisCnf)
    
    # mqtt_publisher.client.loop_start()
    subscribe_topic = ["/TLP/Fre"]
    # mqtt_publisher.subscribe(subscribe_topic)

    # Start a task to handle publishing
    publish_topic = "/Rostek/test_subsribe"
    message = "Hello, MQTT!"
    publish_interval = 5
    # publish_coroutine = publish_task(mqtt_publisher, publish_topic, message, publish_interval)

    # Start the another_task
    # another_coroutine = another_task()
    # production_task = synchronize_production_data(rabbit_publisher, 
    #                                                mqtt_publisher, 
    #                                                redis_db_client, 
    #                                                db_client, 
    #                                                plc_modbus)

    try:
        while True:
            production_task = synchronize_production_data(rabbit_publisher, 
                                   mqtt_publisher, 
                                   redis_db_client, 
                                   db_client, 
                                   plc_modbus)
            quality_task = synchronize_quality_data(rabbit_publisher, 
                                    mqtt_publisher, 
                                    redis_db_client, 
                                    db_client, 
                                    plc_modbus)
            
            machine_task = synchronize_machine_data(rabbit_publisher, 
                                    mqtt_publisher, 
                                    redis_db_client, 
                                    db_client, 
                                    plc_modbus)
            
            monitor_task = capture_store_data(redis_db_client,
                                        db_client,
                                        plc_modbus)
            # await monitor_task
            await asyncio.gather(production_task, quality_task, machine_task, monitor_task, asyncio.sleep(0))

            # await asyncio.gather(production_task, asyncio.sleep(0))

    except KeyboardInterrupt:
        print("KeyboardInterrupt received. Closing the publisher...")
    except Exception as e:
        logging.error(e.__str__())



async def capture_store_data(redis_db_client:RedisMonitor,
                             sql_client:SQLAlchemy,
                             plc_modbus:UvMachine,
                             sleep_time = 2):
    logging.info("Execute capture_store_data()")
    
    for device in plc_modbus.configure["LISTDEVICE"]:
        try:
            logging.debug(device)
            redis_topic_name    = device["ID"] + "/raw"
            logging.debug(f"Topic name: {redis_topic_name}")
            current_data = dict()
            current_data = plc_modbus.read_modbus(current_data)
            
            latest_data = redis_db_client.get_redis_data(redis_topic_name)
            logging.info(f"Current: {current_data}")
            logging.info(f"Old    : {latest_data}")

            updatable = redis_db_client.compare(device["ID"], 
                                            latest_data, 
                                            current_data[device["ID"]])
            if updatable:
                logging.debug("Saving to SQL and Redis ..........")
                redis_db_client.save_to_sql(redis_topic_name, current_data[device["ID"]])
            redis_db_client.save_to_redis(redis_topic_name, current_data[device["ID"]])
            
        except Exception as e:
            logging.error(e.__str__())
        logging.critical("Finish capture_store_data()")
    await asyncio.sleep(sleep_time)

async def synchronize_all_data(rabbit_publisher:rabbit_client.RabbitMQPublisher,
                           mqtt_publisher:mqtt_client.MQTTClient, 
                           redis_db_client:RedisMonitor,
                           sql_client:SQLAlchemy,
                           plc_modbus:UvMachine,
                           to_rabbit=False, to_mqtt=True):
    
    logging.debug("Execute synchronize_data()")
    for device in plc_modbus.configure["LISTDEVICE"]:
        data = None
        try:
            # data = sql_client.session.query(UnsyncedMachineData).order_by(UnsyncedMachineData.id.desc()).first()
            # sql_client.session.close()
            redis_topic = device["ID"] + "/raw"
            data = redis_db_client.get_redis_data(redis_topic)

        except Exception as e:
            logging.error(e)
            data = None
        
        if data is not None:
            logging.debug("Data need to be sent:")
            logging.debug(data)
            try:
                timeNow = int(float(VnTimeStamps.now()))

                production_data = {
                        "record_type"   : "sx",
                        "input"         : data["input"]     if "input"    in data else -1,
                        "output"        : data["output"]    if "output"   in data else -1,
                        "machine_id"    : device["ID"],
                        "timestamp"     : timeNow,
                    }
                
                quality_data = {
                        "record_type"   : "cl",
                        "w_temp"        : data["waterTemp"] if "waterTemp"  in data else -1,
                        "ph"            : data["waterpH"]   if "waterpH"    in data else -1,
                        "t_ev"          : data["envTemp"]   if "envTemp"    in data else -1,
                        "e_hum"         : data["envHum"]    if "envHum"     in data else -1,
                        "uv1"           : data["uv1"]       if "uv1"        in data else -1,
                        "uv2"           : data["uv2"]       if "uv2"        in data else -1,
                        "uv3"           : data["uv3"]       if "uv3"        in data else -1,
                        "p_cut"         : data["p_cut"]     if "p_cut"      in data else -1,
                        "p_conv1"       : data["p_conv"]    if "p_conv"     in data else -1,
                        "p_conv2"       : data["p_conv"]    if "p_conv"     in data else -1,
                        "p_gun"         : data["p_gun"]     if "p_gun"      in data else -1,
                        "machine_id"    : device["ID"],
                        "timestamp"  : timeNow
                    }
                machine_data = {
                        "record_type"   : "tb", 
                        "status"        : data["status"],
                        "type"          : data["errorCode"],
                        "machine_id"    : device["ID"],
                        "timestamp"  : timeNow,
                    }
                
                if to_mqtt:
                    mqtt_publisher.publish(topic= configure.MQTTCnf.PRODUCTIONTOPIC,
                                            data=json.dumps(production_data),
                                            qos=2,
                                            retain=True)
                    mqtt_publisher.publish(topic= configure.MQTTCnf.QUALITYTOPIC,
                                            data=json.dumps(quality_data),
                                            qos=2,
                                            retain=True)
                    mqtt_publisher.publish(topic= configure.MQTTCnf.MACHINETOPIC,
                                            data=json.dumps(machine_data),
                                            qos=2,
                                            retain=True)
                if to_rabbit:
                    logging.debug("Sending data to rabbitMQ")
                    await rabbit_publisher.send_message(json.dumps(data))

                
                # sql_client.session.query(UnsyncedMachineData).filter_by(timestamp=result.timestamp).delete()
                # sql_client.session.commit()
                # sql_client.session.close()
                
                
                logging.debug("Completed!")
            except Exception as e:
                logging.error(e.__str__())
                data = None
        else:
            logging.debug("Data queue is empty!")
    logging.critical(f"production - Sleeping for: {configure.GeneralConfig.DEFAULTRATE}")
    await asyncio.sleep(configure.GeneralConfig.DEFAULTRATE)

async def synchronize_production_data(rabbit_publisher:rabbit_client.RabbitMQPublisher,
                           mqtt_publisher:mqtt_client.MQTTClient, 
                           redis_db_client:RedisMonitor,
                           sql_client:SQLAlchemy,
                           plc_modbus:UvMachine,
                           to_rabbit=False, to_mqtt=True):
    
    logging.critical("Execute synchronize_production_data()")
    for device in plc_modbus.configure["LISTDEVICE"]:
        data = None
        try:
            # data = sql_client.session.query(UnsyncedMachineData).order_by(UnsyncedMachineData.id.desc()).first()
            # sql_client.session.close()
            redis_topic = device["ID"] + "/raw"
            data = redis_db_client.get_redis_data(redis_topic)

        except Exception as e:
            logging.error(e)
            data = None
        
        if data is not None:
            logging.debug("Data need to be sent:")
            logging.debug(data)
            try:
                timeNow = int(float(VnTimeStamps.now()))

                production_data = {
                        "record_type"   : "sx",
                        "input"         : data["input"]     if "input"    in data else -1,
                        "output"        : data["output"]    if "output"   in data else -1,
                        "machine_id"    : device["ID"],
                        "timestamp"     : timeNow,
                    }
                
                
                if to_mqtt:
                    logging.debug("Publish to mqtt....")
                    mqtt_publisher.publish(topic= configure.MQTTCnf.PRODUCTIONTOPIC,
                                            data=json.dumps(production_data),
                                            qos=2,
                                            retain=True)
                logging.debug("Completed!")
            except Exception as e:
                logging.error(e.__str__())
                data = None
        else:
            logging.debug("Data queue is empty!")
    try:
        sleep_time_data = redis_db_client.redis_client.hgetall(configure.RedisCnf.RATETOPIC)
        sleep_time = configure.GeneralConfig.DEFAULTRATE 
        if "production" in sleep_time_data:
            sleep_time = int(sleep_time_data['production'])
        
        logging.critical(f"production - Sleeping for: {sleep_time}")
        await asyncio.sleep(configure.GeneralConfig.DEFAULTRATE)
    
    except Exception as e:
        logging.error(e.__str__())
        logging.critical("Failed to sleep!")
    logging.critical("Finish synchronize_production_data()")

async def synchronize_quality_data(rabbit_publisher:rabbit_client.RabbitMQPublisher,
                           mqtt_publisher:mqtt_client.MQTTClient, 
                           redis_db_client:RedisMonitor,
                           sql_client:SQLAlchemy,
                           plc_modbus:UvMachine,
                           to_rabbit=False, to_mqtt=True):
    
    logging.debug("Execute synchronize_data()")
    for device in plc_modbus.configure["LISTDEVICE"]:
        data = None
        try:
            # data = sql_client.session.query(UnsyncedMachineData).order_by(UnsyncedMachineData.id.desc()).first()
            # sql_client.session.close()
            redis_topic = device["ID"] + "/raw"
            data = redis_db_client.get_redis_data(redis_topic)

        except Exception as e:
            logging.error(e)
            data = None
        
        if data is not None:
            logging.debug("Data need to be sent:")
            logging.debug(data)
            try:
                timeNow = int(float(VnTimeStamps.now()))

                quality_data = {
                        "record_type"   : "cl",
                        "w_temp"        : data["waterTemp"] if "waterTemp"  in data else -1,
                        "ph"            : data["waterpH"]   if "waterpH"    in data else -1,
                        "t_ev"          : data["envTemp"]   if "envTemp"    in data else -1,
                        "e_hum"         : data["envHum"]    if "envHum"     in data else -1,
                        "uv1"           : data["uv1"]       if "uv1"        in data else -1,
                        "uv2"           : data["uv2"]       if "uv2"        in data else -1,
                        "uv3"           : data["uv3"]       if "uv3"        in data else -1,
                        "p_cut"         : data["p_cut"]     if "p_cut"      in data else -1,
                        "p_conv1"       : data["p_conv"]    if "p_conv"     in data else -1,
                        "p_conv2"       : data["p_conv"]    if "p_conv"     in data else -1,
                        "p_gun"         : data["p_gun"]     if "p_gun"      in data else -1,
                        "machine_id"    : device["ID"],
                        "timestamp"  : timeNow
                    }
                
                
                if to_mqtt:
                    mqtt_publisher.publish(topic= configure.MQTTCnf.QUALITYTOPIC,
                                            data=json.dumps(quality_data),
                                            qos=2,
                                            retain=True)
                logging.debug("Completed!")
            except Exception as e:
                logging.error(e.__str__())
                data = None
        else:
            logging.debug("Data queue is empty!")
    
    try:
        sleep_time_data = redis_db_client.redis_client.hgetall(configure.RedisCnf.RATETOPIC)
        sleep_time = configure.GeneralConfig.DEFAULTRATE 
        if "quality" in sleep_time_data:
            sleep_time = int(sleep_time_data['quality'])
        
        logging.critical(f"quality - Sleeping for: {sleep_time}")
        await asyncio.sleep(configure.GeneralConfig.DEFAULTRATE)
    
    except Exception as e:
        logging.error(e.__str__())
        logging.critical("Failed to sleep!")
    logging.critical("Finish synchronize_quality_data()")

async def synchronize_machine_data(rabbit_publisher:rabbit_client.RabbitMQPublisher,
                           mqtt_publisher:mqtt_client.MQTTClient, 
                           redis_db_client:RedisMonitor,
                           sql_client:SQLAlchemy,
                           plc_modbus:UvMachine,
                           to_rabbit=False, to_mqtt=True):
    
    logging.debug("Execute synchronize_data()")
    for device in plc_modbus.configure["LISTDEVICE"]:
        data = None
        try:
            # data = sql_client.session.query(UnsyncedMachineData).order_by(UnsyncedMachineData.id.desc()).first()
            # sql_client.session.close()
            redis_topic = device["ID"] + "/raw"
            data = redis_db_client.get_redis_data(redis_topic)

        except Exception as e:
            logging.error(e)
            data = None
        
        if data is not None:
            logging.debug("Data need to be sent:")
            logging.debug(data)
            try:
                timeNow = int(float(VnTimeStamps.now()))

                machine_data = {
                        "record_type"   : "tb", 
                        "status"        : data["status"],
                        "type"          : data["errorCode"],
                        "machine_id"    : device["ID"],
                        "timestamp"  : timeNow,
                    }
                
                if to_mqtt:
                    mqtt_publisher.publish(topic= configure.MQTTCnf.MACHINETOPIC,
                                            data=json.dumps(machine_data),
                                            qos=2,
                                            retain=True)
                logging.debug("Completed!")
            except Exception as e:
                logging.error(e.__str__())
                data = None
        else:
            logging.debug("Data queue is empty!")
    
    try:
        sleep_time_data = redis_db_client.redis_client.hgetall(configure.RedisCnf.RATETOPIC)
        sleep_time = configure.GeneralConfig.DEFAULTRATE 
        if "machine" in sleep_time_data:
            sleep_time = int(sleep_time_data['machine'])
        
        logging.critical(f"machine - Sleeping for: {sleep_time}")
        await asyncio.sleep(configure.GeneralConfig.DEFAULTRATE)
    
    except Exception as e:
        logging.error(e.__str__())
        logging.critical("Failed to sleep!")
    logging.critical("Finish synchronize_machine_data()")
