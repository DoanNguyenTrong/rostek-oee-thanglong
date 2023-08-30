from app.model.data_model import MachineData
import logging, time, json
from configure import *
from sqlalchemy import and_
from app.machine.printing_machine import PRINTING_MACHINE
from app.machine.box_folding_machine import BOX_FOLDING_MACHINE
from app.machine.cutting_machine import CUTTING_MACHINE
from app.machine.uv_machine import UV_MACHINE
from utils.threadpool import ThreadPool
import utils.vntime as VnTimeStamps
import schedule
from utils.getip import get_ip
from utils.getuptime import get_uptime
from app import redisClient, mqttService

workers = ThreadPool(10)

def init_objects():
    """
    Create instance of machine object and start related functions
    """
    logging.warning("Starting program")
    printingMachine     = PRINTING_MACHINE(redisClient, printingMachineConfigure)
    boxFoldingMachine   = BOX_FOLDING_MACHINE(redisClient, boxFoldingMachineConfigure)
    uvMachine           = UV_MACHINE(redisClient, uvMachineConfigure)
    cuttingMachine      = CUTTING_MACHINE(redisClient, cuttingMachineConfigure)
    start_service(printingMachine, boxFoldingMachine, cuttingMachine, uvMachine)

def start_read_modbus_device(*args):
    while True:
        for arg in args:
            arg.start_reading_modbus()

def start_service(*args):
    """
    Start instance's internal function
    """
    for object in args:
        workers.add_task(object.start)
    workers.add_task(start_read_modbus_device,*args)

def sync_production_data():
    """
    Sync production data
    """
    timeNow = int(float(VnTimeStamps.now()))
    for configure in listConfig:
        for device in configure["LISTDEVICE"]:
            data = redisClient.hgetall(device["ID"] + "/raw")
            if data:
                sendData = {
                    "record_type"   : "sx",
                    "input"         : data["input"]             if "input"          in data else -1,
                    "output"        : data["output"]            if "output"         in data else -1,
                    "machine_id"    : device["ID"],
                    "timestamp"     : timeNow,
                }
                logging.warning(sendData)
                try:
                    mqttService.publish(MQTTCnf.PRODUCTIONTOPIC, json.dumps(sendData))
                    # logging.warning("Complete send production data")
                except:
                    pass
            
def sync_quality_data():
    """
    Send quality data
    """
    timeNow = int(float(VnTimeStamps.now()))
    for configure in listConfig:
        for device in configure["LISTDEVICE"]:
            data = redisClient.hgetall(device["ID"] + "/raw")
            if data:
                sendData = {
                    "record_type"   : "cl",
                    "w_temp"        : data["waterTemp"]             if "waterTemp"          in data else -1,
                    "ph"            : data["waterpH"]               if "waterpH"            in data else -1,
                    "t_ev"          : data["envTemp"]               if "envTemp"            in data else -1,
                    "t_gun"         : data["glueTemp"]              if "glueTemp"           in data else -1,
                    "e_hum"         : data["envHum"]                if "envHum"             in data else -1,
                    "uv1"           : data["uv1"]                   if "uv1"                in data else -1,
                    "uv2"           : data["uv2"]                   if "uv2"                in data else -1,
                    "uv3"           : data["uv3"]                   if "uv3"                in data else -1,
                    "p_conv1"       : data["upperAirPressure"]      if "upperAirPressure"   in data else -1,
                    "p_conv2"       : data["lowerAirPressure"]      if "lowerAirPressure"   in data else -1,
                    "p_gun"         : data["gluePressure"]          if "gluePressure"       in data else -1,
                    "machine_id"    : device["ID"],
                    "timestamp"  : timeNow
                }
                logging.warning(sendData)
                try:
                    mqttService.publish(MQTTCnf.QUALITYTOPIC, json.dumps(sendData))
                    # logging.warning("Complete send quality data")
                except:
                    pass

def sync_machine_data():
    """
    Send machine data
    """
    timeNow = int(float(VnTimeStamps.now()))
    for configure in listConfig:
        for device in configure["LISTDEVICE"]:
            data = redisClient.hgetall(device["ID"] + "/raw")
            if data:
                sendData = {
                    "record_type"   : "tb", 
                    "status"        : data["status"],
                    "type"          : data["errorCode"],
                    "machine_id"    : device["ID"],
                    "timestamp"     : timeNow,
                }
                logging.warning(sendData)
                try:
                    mqttService.publish(MQTTCnf.MACHINETOPIC, json.dumps(sendData))
                    # logging.warning("Complete send machine data")
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
                "timestamp"       : result.timestamp,
                "temperature"     : result.temperature,
                "humidity"        : result.humidity,
                "isChanging"      : result.isChanging
            }
        )
    return data

def handle_request_data(data,client):
    """
    Handle data request from server
    """
    deviceId    = data["machine_id"]
    timeFrom    = data["time_start"]
    timeTo      = data["time_end"]
    data = query_data(str(deviceId, timeFrom, timeTo))
    client.publish(json.dumps(data))

def query_data(deviceId,timeFrom,timeTo):
    """
    Query data for request
    """
    data = []
    results = MachineData.query.filter(and_(MachineData.timestamp >= timeFrom,MachineData.timestamp <= timeTo, MachineData.deviceId == deviceId)).all()
    if results:
        for result in results:
            data.append(
                {
                    "deviceId"          : result.deviceId,
                    "machineStatus"     : result.machineStatus,
                    "output"            : result.output,
                    "input"             : result.input,
                    "envTemp"           : result.envTemp,
                    "envHum"            : result.envHum,
                    "waterTemp"         : result.waterTemp,
                    "waterpH"           : result.waterpH,
                    "timestamp"         : result.timestamp,
                    "uv1"               : result.uv1,
                    "uv2"               : result.uv2,
                    "uv3"               : result.uv3,
                    "upperAirPressure"  : result.upperAirPressure,
                    "lowerAirPressure"  : result.lowerAirPressure,
                    "gluePressure"      : result.gluePressure,
                    "glueTemp"          : result.glueTemp
                }
            )
        return data
    else:
        return -1

def cmd_handler(payload):
    try:
        mqttService.publish("/gateway/reply", json.dumps({
            "local_ip"          : get_ip(),
            "machine_count"     : MachineData.query.count(),
            "gateway_uptime"    : get_uptime(),
        }))
    except Exception as e:
        logging.error(str(e))
         
def handle_rate_data(client,data,redisClient):
    """
    Handle refresh data rate
    """
    activeScheduling = False
    schedule.clear()
    recordType = data["record_type"]
    if recordType == "sx":
        redisClient.hset(RedisCnf.RATETOPIC, "production", data["frequency"])

    elif recordType == "cl":
        redisClient.hset(RedisCnf.RATETOPIC, "quality", data["frequency"])

    elif recordType == "tb":
        redisClient.hset(RedisCnf.RATETOPIC, "machine", data["frequency"])

    activeScheduling = True
    start_sync_service()
    # logging.error(f"Scheduled every {data['frequency']} secs for {recordType} !")

def handle_request_data(deviceId,data,client):
    """
    Handle data request from server
    """
    timeFrom    = data["from"]
    timeTo      = data["to"]
    data = query_data(str(deviceId, timeFrom, timeTo))
    client.publish(json.dumps(data))

def start_scheduling_thread():
    """
    Thread to schedule service
    """
    while activeScheduling:
        schedule.run_pending()
        time.sleep(1)

def start_sync_service():
    """
    Start scheduling for syncing at default sending rate and scheduling service
    """
    rate = redisClient.hgetall(RedisCnf.RATETOPIC)
    if "machine" not in rate:
        machineRate = GeneralConfig.DEFAULTRATE 
    else:
        machineRate = int(rate["machine"])
    if "quality" not in rate:
        qualityRate = GeneralConfig.DEFAULTRATE 
    else:
        qualityRate = int(rate["quality"])
    if "production" not in rate:
        productionRate = GeneralConfig.DEFAULTRATE 
    else:
        productionRate = int(rate["production"])

    schedule.every(machineRate).seconds.do(sync_machine_data)
    schedule.every(qualityRate).seconds.do(sync_quality_data)
    schedule.every(productionRate).seconds.do(sync_production_data)
    workers.add_task(start_scheduling_thread)

activeScheduling = True
start_sync_service()