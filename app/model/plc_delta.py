import time
from pymodbus.client.sync import ModbusSerialClient
import logging
from configure import  GeneralConfig
import struct
import utils.vntime as VnTimeStamps
from configure import *
import json 
import utils.vntime as VnTimestamps

class DELTA_SA2():
    def __init__(self,redisClient, configure):
        self.__redisClient       = redisClient
        self.__modbusConnection  = False
        self.__kernelActive      = False
        self.__configure         = configure
        self.deviceData          = {}
        self.__startup = int(float(VnTimeStamps.now()))
        self.__get_redis_data()

    def start(self):
        """
        Khởi tạo đọc dữ liệu modbus
        """
        self.__kernelActive = True
        logging.warning("Init Kernel successful")
        self.__connect_modbus()
        self.__start_reading_modbus()
       
    def __get_redis_data(self):
        """
        Load dữ liệu cũ từ REDIS
        """
        for device in self.__configure["LISTDEVICE"]:
            deviceId    = device["ID"]
            rawTopic    = "/device/V2/" + device["ID"] + "/raw"
            deviceData  = self.__redisClient.hgetall(rawTopic)

            self.deviceData[deviceId]          = {}
            self.deviceData[deviceId]["now"]   = int(float(VnTimeStamps.now()))
            if "RunningNumber" not in deviceData:
                self.deviceData[deviceId]["RunningNumber"] = 0
                self.deviceData[deviceId]["lastStatus"]    = STATUS.DISCONNECT
            else:
                self.deviceData[deviceId]["RunningNumber"] = int(deviceData["RunningNumber"]) 

    def __connect_modbus(self):
        """
        Khởi tạo kết nối MODBUS RTU
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
        Lưu dữ liệu vào redis
        """
        # logging.info(topic)
        for key in data.keys():
            self.__redisClient.hset(topic,key ,data[key])

    def __parse_register_data(self,c,id1,id2):
        """
        Parse dữ liệu modbus
        """
        a = c[id1]
        b = c[id2]
        s = struct.pack(">l", (b<<16)|a)
        return struct.unpack(">l", s)[0]

    def __start_reading_modbus(self):
        """
        Bắt đầu đọc data của những thiết bị 
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
                        self.deviceData[deviceId]["MCStatus"] = STATUS.DISCONNECT
                    self.__save_raw_data_to_redis(rawTopic,self.deviceData[deviceId])
            time.sleep(GeneralConfig.READINGRATE)

    def __read_modbus_data(self,device,deviceId):
        """
        Tạo request đọc modbus và parse data 
        """
        r = self.__modbusMaster.read_holding_registers(
            address = device["ADDRESS"], 
            count   = device["COUNT"], 
            unit    = device["UID"]
        )
        # logging.warning(f"{device['ID']} --- {r}")
        registerData = r.registers
        if int(registerData[5]) == 1:
            mcstatus = STATUS.RUN
        elif int(registerData[5]) == 2:
            mcstatus = STATUS.IDLE
        else:
            mcstatus = STATUS.ERROR

        actual = int(registerData[1])

        if self.__is_status_change(deviceId,mcstatus) or self.__is_actual_change(deviceId, actual):
            timeNow = VnTimeStamps.now()
            self.deviceData[deviceId]["timestamp"]  = timeNow
            eventTopic = deviceId + "event"
            self.__redisClient.lpush(eventTopic ,json.dumps(self.deviceData[deviceId]))

    def __is_status_change(self, deviceId, status):
        """
        Check if machine status change
        """
        if self.deviceData[deviceId]["MCStatus"] != status:
            self.deviceData[deviceId]["MCStatus"] = status
            return True
        return False
        
    def __is_actual_change(self, deviceId, actual):
        """
        Check if actual change
        """
        if self.deviceData[deviceId]["actual"] != actual:
            self.deviceData[deviceId]["actual"] = actual
            return True
        return False
    
    def __is_ng_change(self, deviceId, ng):
        """
        Check if ng change
        """
        if self.deviceData[deviceId]["ng"] != ng:
            self.deviceData[deviceId]["ng"] = ng
            return True
        return False
    
    def __is_running_number_change(self, deviceId, runningNumber):
        """
        Check if running_number change
        """
        if self.deviceData[deviceId]["runningNumber"] != runningNumber:
            self.deviceData[deviceId]["runningNumber"] = runningNumber
            return True
        return False

    

        