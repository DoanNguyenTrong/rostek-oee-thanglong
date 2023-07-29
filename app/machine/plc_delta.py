from pymodbus.client.sync import ModbusSerialClient
import logging, json, struct, time
import utils.vntime as VnTimeStamps
from configure import *
from ..model.data_model import MachineData
from ..model.unsynced_data import UnsyncedMachineData
from sqlalchemy.orm import Session
from app import db

class DELTA_SA2():
    def __init__(self,redisClient, configure):
        self.__redisClient          = redisClient
        self.__modbusConnection     = False
        self.__kernelActive         = False
        self.__configure            = configure
        self.deviceData             = {}
        self.__get_redis_data()

    def start(self):
        """
        Start function
        """
        self.__kernelActive = True
        logging.warning("Init Kernel successful")
        self.__connect_modbus()
        self.__start_reading_modbus()
       
    def __get_redis_data(self):
        """
        Load old data from redis
        """
        for device in self.__configure["LISTDEVICE"]:
            deviceId    = device["ID"]
            rawTopic    = "/device/V2/" + device["ID"] + "/raw"
            deviceData  = self.__redisClient.hgetall(rawTopic)
            self.deviceData[deviceId]               = {}
            self.deviceData[deviceId]["timestamp"]  = int(float(VnTimeStamps.now()))
            if "runningNumber" not in deviceData:
                self.deviceData[deviceId]["runningNumber"]  = 0
                self.deviceData[deviceId]["status"]         = STATUS.DISCONNECT
                self.deviceData[deviceId]["actual"]         = 0
                self.deviceData[deviceId]["ng"]             = 0
                self.deviceData[deviceId]["changeProduct"]  = 0
            else:
                self.deviceData[deviceId]["runningNumber"]  = int(deviceData["runningNumber"]) 
                self.deviceData[deviceId]["status"]         = int(deviceData["status"]) 
                self.deviceData[deviceId]["actual"]         = int(deviceData["actual"]) 
                self.deviceData[deviceId]["ng"]             = int(deviceData["ng"]) 
                self.deviceData[deviceId]["changeProduct"]  = int(deviceData["changeProduct"])

    def __connect_modbus(self):
        """
        Init MODBUS RTU connection
        """
        try:
            logging.error(self.__configure)
            self.__modbusMaster = ModbusSerialClient(
                method      = self.__configure["METHOD"], 
                port        = self.__configure["PORT"], 
                timeout     = self.__configure["TIMEOUT"], 
                baudrate    = self.__configure["BAUDRATE"]
            )
            self.__modbusMaster.connect()
            self.__modbusConnection = True
        except Exception as e:
            self.__modbusConnection = False
            logging.error(str(e))

    def __save_raw_data_to_redis(self, topic, data):
        """
        Save raw data to redis
        """
        # logging.info(topic)
        for key in data.keys():
            self.__redisClient.hset(topic,key ,data[key])

    def __parse_register_data(self,c,id1,id2):
        """
        Parse modbus data
        """
        a = c[id1]
        b = c[id2]
        s = struct.pack(">l", (b<<16)|a)
        return struct.unpack(">l", s)[0]

    def __start_reading_modbus(self):
        """
        Start reading modbus from device 
        """
        while self.__kernelActive:
            if not self.__modbusConnection:
                self.__connect_modbus()
            else:
                for device in self.__configure["LISTDEVICE"]:
                    deviceId                                = device["ID"]
                    self.deviceData[deviceId]["Device_id"]  = deviceId
                    rawTopic                                = "/device/V2/" + deviceId + "/raw"
                    try:
                        self.__read_modbus_data(device,deviceId)
                    except Exception as e:
                        logging.error(str(e))
                        self.deviceData[deviceId]["status"] = STATUS.DISCONNECT
                    self.__save_raw_data_to_redis(rawTopic,self.deviceData[deviceId])
            time.sleep(GeneralConfig.READINGRATE)

    def __read_modbus_data(self,device,deviceId):
        """
        Make request to read modbus and parse data 
        """
        r = self.__modbusMaster.read_holding_registers(
            address = device["ADDRESS"], 
            count   = device["COUNT"], 
            unit    = device["UID"]
        )
        # logging.warning(f"{device['ID']} --- {r}")
        registerData = r.registers
        # logging.error(f"Actual - {r.registers[1]}")
        # logging.error(f"Status - {r.registers[5]}")
        # logging.error(f"ChangeProduct - {r.registers[11]}")
        if int(registerData[5]) == 1:
            status = STATUS.RUN
        elif int(registerData[5]) == 2:
            status = STATUS.IDLE
        else:
            status = STATUS.ERROR

        actual          = int(registerData[1])
        temperature     = float(registerData[5])
        humidity        = float(registerData[1])
        changeProduct   = int(registerData[11])
        self.deviceData[deviceId]["temperature"]    = temperature
        self.deviceData[deviceId]["humidity"]       = humidity

        statusChange    = self.__is_status_change(deviceId,status)
        actualChange    = self.__is_actual_change(deviceId,actual)
        changingProduct = self.__is_changing_product(deviceId,changeProduct)
        # logging.warning(self.deviceData[deviceId])
        if statusChange or actualChange or changingProduct:
            timeNow = int(float(VnTimeStamps.now()))
            self.deviceData[deviceId]["timestamp"]  = timeNow
            insertData = MachineData(
                deviceId            = deviceId, 
                machineStatus       = status,
                actual              = actual,
                timestamp           = timeNow,
                humidity            = humidity,
                runningNumber       = self.deviceData[deviceId]["runningNumber"],
                temperature         = temperature,
                isChanging          = changeProduct
                )
            insertUnsyncedData = UnsyncedMachineData(
                deviceId            = deviceId, 
                machineStatus       = status,
                actual              = actual,
                timestamp           = timeNow,
                humidity            = humidity,
                runningNumber       = self.deviceData[deviceId]["runningNumber"],
                temperature         = temperature,
                isChanging          = changeProduct
                )
            try:
                db.session.add(insertData)
                db.session.add(insertUnsyncedData)
                db.session.commit()
                db.session.close() 
            except:
                db.session.rollback()
                db.session.close() 
            logging.error("Complete saving data!")

    def __is_status_change(self, deviceId, status):
        """
        Check if machine status change
        """
        if self.deviceData[deviceId]["status"] != status:
            logging.error(f"Status change, previous status: {self.deviceData[deviceId]['status']} - current status {status}")
            self.deviceData[deviceId]["status"] = status
            return True
        return False
        
    def __is_actual_change(self, deviceId, actual):
        """
        Check if actual change
        """
        if self.deviceData[deviceId]["actual"] != actual:
            logging.error(f"Actual change, previous actual: {self.deviceData[deviceId]['actual']} - current actual {actual}")
            self.deviceData[deviceId]["actual"] = actual
            return True
        return False
    
    def __is_changing_product(self, deviceId, changeProduct):
        """
        Check if changing product
        """
        now = VnTimeStamps.now()
        # if self.deviceData[deviceId]["changeProduct"] != changeProduct:
        #     logging.error(f"Changing product, previous product: {self.deviceData[deviceId]['changeProduct']} - current product {changeProduct}")
        #     self.deviceData[deviceId]["changeProduct"] = changeProduct
        #     self.deviceData[deviceId]["runningNumber"] += 1
        #     return True
        if self.deviceData[deviceId]["changeProduct"] == 0 and changeProduct == 1:
            logging.error(f"Start changing product, previous running number: {self.deviceData[deviceId]['runningNumber']}")
            self.deviceData[deviceId]["changeProduct"] = changeProduct
            return True
        elif self.deviceData[deviceId]["changeProduct"] == 1 and changeProduct == 0:
            self.deviceData[deviceId]["runningNumber"] += 1
            logging.error(f"Stop changing product, current running number: {self.deviceData[deviceId]['runningNumber']} ")
            self.deviceData[deviceId]["changeProduct"] = changeProduct
            return True
        else:
            return False
    # def __is_ng_change(self, deviceId, ng):
    #     """
    #     Check if ng change
    #     """
    #     if self.deviceData[deviceId]["ng"] != ng:
    #         self.deviceData[deviceId]["ng"] = ng
    #         return True
    #     return False

    


