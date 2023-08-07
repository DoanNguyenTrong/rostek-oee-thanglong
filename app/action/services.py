import logging
import time
import json
import asyncio
from flask_sqlalchemy import SQLAlchemy

import app.mqtt_client as mqtt_client
import configure 
import app.rabbit_client as rabbit_client
from app.machine.base_modbus import BaseModbusPLC
from app.machine.devices import UvMachine, BoxFoldingMachine, CuttingMachine, PrintingMachine
from app.redis_client import RedisMonitor
from app.model.data_model import MachineData, UnsyncedMachineData
from app.utils import vntime as VnTimeStamps
from app import db_client


async def publish_task(mqtt_handler, publish_topic, message, publish_interval):
    while True:
        mqtt_handler.publish(publish_topic, message)
        await asyncio.sleep(publish_interval)




async def rostek_oee(rabbit_publisher: rabbit_client.RabbitMQPublisher,
               mqtt_publisher: mqtt_client.MQTTClient,
               redis_obj):
    """
    Create instance of machine object and start related functions
    """
    logging.critical("Starting program ...")
    
    # hardware device
    logging.critical("Initialize PLC modules ...")
    plc_uv  = UvMachine(configure.uvMachineConfigure)
    plc_box_folding = BoxFoldingMachine(configure.boxFoldingMachineConfigure)
    plc_cutting = CuttingMachine(configure=configure.cuttingMachineConfigure)
    plc_printing = PrintingMachine(configure=configure.printingMachineConfigure)

    # plc_modbus = [plc_uv, plc_box_folding, plc_cutting, plc_printing]
    all_plc_devices = [plc_uv]

    logging.critical("Initialize data publisher: MQTT, RabbitMQ")
    redis_db_client = RedisMonitor(redis_client=redis_obj,
                                sql_database_client=db_client,
                                configure=configure.RedisCnf)
    
    mqtt_publisher.connect(keep_alive=True)
    # mqtt_publisher.subscribe([configure.MQTTCnf.RATETOPIC])

    await rabbit_publisher.connect(routing_key=['oee_data'])
    
    logging.critical("Initialize coroutines...")
    # All coroutines defined
    production_coroutine = production_loop(rabbit_publisher, 
                                        mqtt_publisher, 
                                        redis_db_client, 
                                        db_client, 
                                        all_plc_devices)
    quality_coroutine = quality_loop(rabbit_publisher, 
                                    mqtt_publisher, 
                                    redis_db_client, 
                                    db_client, 
                                    all_plc_devices)
    
    machine_coroutine = machine_loop(rabbit_publisher, 
                                    mqtt_publisher, 
                                    redis_db_client, 
                                    db_client, 
                                    all_plc_devices)
    
    device_coroutine = capture_loop(redis_db_client,
                                        db_client,
                                        all_plc_devices)
    logging.critical("Enter main loop ...")
    try:
        while True:
            await asyncio.gather(device_coroutine, 
                                 production_coroutine,
                                 quality_coroutine,
                                 machine_coroutine,
                                 asyncio.sleep(0))

            # await asyncio.gather(production_task, asyncio.sleep(0))
            
    except KeyboardInterrupt:
        print("KeyboardInterrupt received. Closing the publisher...")
    except Exception as e:
        logging.error(e.__str__())


async def capture_store_data(redis_db_client:RedisMonitor,
                             sql_client:SQLAlchemy,
                             plc_devices:list,
                             sleep_time = 1):
    logging.info("Execute capture_store_data()")
    for device in plc_devices:
        for device_configure in device.configure["LISTDEVICE"]:
            try:
                logging.debug(device_configure)
                redis_topic_name    = device_configure["ID"] + "/raw"
                logging.debug(f"Topic name: {redis_topic_name}")
                current_data = dict()
                current_data = device.read_modbus(current_data)
                
                latest_data = redis_db_client.get_redis_data(redis_topic_name)
                logging.info(f"Current: {current_data}")
                logging.info(f"Old    : {latest_data}")

                updatable = redis_db_client.compare(device_configure["ID"], 
                                                latest_data, 
                                                current_data[device_configure["ID"]])
                if updatable:
                    logging.debug("Saving to SQL and Redis ..........")
                    redis_db_client.save_to_sql(redis_topic_name, current_data[device_configure["ID"]])
                redis_db_client.save_to_redis(redis_topic_name, current_data[device_configure["ID"]])
                
            except Exception as e:
                logging.error(e.__str__())
            logging.critical("Finish capture_store_data()")
        await asyncio.sleep(sleep_time)

async def capture_loop(redis_db_client:RedisMonitor,
                             sql_client:SQLAlchemy,
                             plc_devices:list,
                             sleep_time = 1):
    current_time =VnTimeStamps.now()
    while True:
        await capture_store_data(redis_db_client,
                                db_client,
                                plc_devices)
        
        execute_time = VnTimeStamps.now() - current_time
        sleep_time -= execute_time
        sleep_time = sleep_time if sleep_time > 0 else 0
        logging.critical(f"capture_loop() sleeping for: {sleep_time}")
        await asyncio.sleep(sleep_time)
    
        logging.critical("Finish  capture_loop()")
        logging.critical(f"capture_loop() time: {VnTimeStamps.now() - current_time}")
        current_time = VnTimeStamps.now()


async def synchronize_all_data(rabbit_publisher:rabbit_client.RabbitMQPublisher,
                           mqtt_publisher:mqtt_client.MQTTClient, 
                           redis_db_client:RedisMonitor,
                           sql_client:SQLAlchemy,
                           plc_devices:list,
                           to_rabbit=False, to_mqtt=True):
    
    logging.debug("Execute synchronize_data()")
    for machine in plc_devices:
        for device in machine.configure["LISTDEVICE"]:
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
                           plc_devices:list,
                           to_rabbit=False, to_mqtt=True):
    start_time = VnTimeStamps.now()
    logging.critical("Execute synchronize_production_data()")
    for machine in plc_devices:
        for device in machine.configure["LISTDEVICE"]:
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
        
    end_time = VnTimeStamps.now()
    logging.critical(f"Execute synchronize_production_data(), time: {end_time-start_time}")

async def synchronize_quality_data(rabbit_publisher:rabbit_client.RabbitMQPublisher,
                           mqtt_publisher:mqtt_client.MQTTClient, 
                           redis_db_client:RedisMonitor,
                           sql_client:SQLAlchemy,
                           plc_devices:list,
                           to_rabbit=False, to_mqtt=True):
    
    start_time = VnTimeStamps.now()
    logging.debug("Execute synchronize_data()")
    
    for machine in plc_devices:
        for device in machine.configure["LISTDEVICE"]:
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
    
    end_time = VnTimeStamps.now()
    logging.critical(f"Execute synchronize_quality_data(), time: {end_time-start_time}")

async def synchronize_machine_data(rabbit_publisher:rabbit_client.RabbitMQPublisher,
                           mqtt_publisher:mqtt_client.MQTTClient, 
                           redis_db_client:RedisMonitor,
                           sql_client:SQLAlchemy,
                           plc_devices:UvMachine,
                           to_rabbit=False, to_mqtt=True):
    
    start_time = VnTimeStamps.now()
    logging.debug("Execute synchronize_machine_data()")
    for machine in plc_devices:
        for device in machine.configure["LISTDEVICE"]:
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
    
    end_time = VnTimeStamps.now()
    logging.critical(f"Execute synchronize_machine_data(), time: {end_time-start_time}")

async def production_loop(rabbit_publisher:rabbit_client.RabbitMQPublisher,
                           mqtt_publisher:mqtt_client.MQTTClient, 
                           redis_db_client:RedisMonitor,
                           sql_client:SQLAlchemy,
                           plc_devices:list,
                           to_rabbit=False, to_mqtt=True):
    current_time =VnTimeStamps.now()
    while True:
        await synchronize_production_data(rabbit_publisher, 
                                        mqtt_publisher, 
                                        redis_db_client, 
                                        db_client, 
                                        plc_devices,
                                        to_rabbit=to_rabbit,
                                        to_mqtt=to_mqtt)
        try:            
            sleep_time_data = redis_db_client.redis_client.hgetall(configure.RedisCnf.RATETOPIC)
            sleep_time = configure.GeneralConfig.DEFAULTRATE 
            if "production" in sleep_time_data:
                sleep_time = int(sleep_time_data['production'])
            
            execute_time = VnTimeStamps.now() - current_time
            sleep_time -= execute_time
            sleep_time = sleep_time if sleep_time > 0 else 0
            logging.critical(f"production - Sleeping for: {sleep_time}")
            await asyncio.sleep(sleep_time)

        except Exception as e:
            logging.error(e.__str__())
            logging.critical("Failed to sleep!")
        
        logging.critical("Finish  production_loop()")
        logging.critical(f"production_loop() time: {VnTimeStamps.now() - current_time}")
        current_time = VnTimeStamps.now()

async def quality_loop(rabbit_publisher:rabbit_client.RabbitMQPublisher,
                           mqtt_publisher:mqtt_client.MQTTClient, 
                           redis_db_client:RedisMonitor,
                           sql_client:SQLAlchemy,
                           plc_devices:list,
                           to_rabbit=False, to_mqtt=True):
    current_time =VnTimeStamps.now()
    while True:
        await synchronize_quality_data(rabbit_publisher, 
                                    mqtt_publisher, 
                                    redis_db_client, 
                                    db_client, 
                                    plc_devices)
        try:
            sleep_time_data = redis_db_client.redis_client.hgetall(configure.RedisCnf.RATETOPIC)
            sleep_time = configure.GeneralConfig.DEFAULTRATE 
            if "quality" in sleep_time_data:
                sleep_time = int(sleep_time_data['quality'])
            
            execute_time = VnTimeStamps.now() - current_time
            sleep_time -= execute_time
            sleep_time = sleep_time if sleep_time > 0 else 0
            logging.critical(f"quality - Sleeping for: {sleep_time}")
            await asyncio.sleep(sleep_time)
       
        except Exception as e:
            logging.error(e.__str__())
            logging.critical("Failed to sleep!")
        logging.critical("Finish  quality_loop()")
        logging.critical(f"quality_loop() time: {VnTimeStamps.now() - current_time}")
        current_time = VnTimeStamps.now()

async def machine_loop(rabbit_publisher:rabbit_client.RabbitMQPublisher,
                           mqtt_publisher:mqtt_client.MQTTClient, 
                           redis_db_client:RedisMonitor,
                           sql_client:SQLAlchemy,
                           plc_devices:list,
                           to_rabbit=False, to_mqtt=True):
    current_time =VnTimeStamps.now()
    while True:
        await synchronize_machine_data(rabbit_publisher, 
                                    mqtt_publisher, 
                                    redis_db_client, 
                                    db_client, 
                                    plc_devices)
        try:
            sleep_time_data = redis_db_client.redis_client.hgetall(configure.RedisCnf.RATETOPIC)
            sleep_time = configure.GeneralConfig.DEFAULTRATE 
            if "machine" in sleep_time_data:
                sleep_time = int(sleep_time_data['machine'])
            
            execute_time = VnTimeStamps.now() - current_time
            sleep_time -= execute_time
            sleep_time = sleep_time if sleep_time > 0 else 0
            logging.critical(f"machine - Sleeping for: {sleep_time}")
            await asyncio.sleep(sleep_time)
        
        except Exception as e:
            logging.error(e.__str__())
            logging.critical("Failed to sleep!")
        logging.critical("Finish  machine_loop()")
        logging.critical(f"machine_loop() time: {VnTimeStamps.now() - current_time}")
        current_time = VnTimeStamps.now()
