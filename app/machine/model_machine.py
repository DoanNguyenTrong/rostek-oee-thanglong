from pymodbus.client.sync import ModbusSerialClient
import logging, json, struct, time
import utils.vntime as VnTimeStamps
from configure import *
from ..model.data_model import MachineData
from app import db
# from app.mqtt_service import mqtt_client
from app import mqtt_client

class MACHINE():
    def __init__(self,redisClient, configure):
        self._redisClient          = redisClient
        self._modbusConnection     = False
        self._kernelActive         = False
        self._configure            = configure
        self.deviceData             = {}
        self._get_redis_data()

    def start(self):
        """
        Start function
        """
        self._kernelActive = True
        logging.warning("Init Kernel successful")
        self._connect_modbus()
        self._start_reading_modbus()
       
    def _get_redis_data(self):
        """
        Load old data from redis
        """
        for device in self._configure["LISTDEVICE"]:
            deviceId    = device["ID"]
            rawTopic    = device["ID"] + "/raw"
            deviceData  = self._redisClient.hgetall(rawTopic)
            self.deviceData[deviceId]               = {}
            self.deviceData[deviceId]["timestamp"]  = int(float(VnTimeStamps.now()))
            if "input" not in deviceData:
                self.deviceData[deviceId]["status"]         = STATUS.DISCONNECT
                self.deviceData[deviceId]["output"]         = 0
                self.deviceData[deviceId]["input"]          = 0
                self.deviceData[deviceId]["changeProduct"]  = 0
                self.deviceData[deviceId]["errorCode"]      = 0
            else:
                self.deviceData[deviceId]["status"]         = int(deviceData["status"]) 
                self.deviceData[deviceId]["output"]         = int(deviceData["output"]) 
                self.deviceData[deviceId]["input"]          = int(deviceData["input"])
                self.deviceData[deviceId]["changeProduct"]  = int(deviceData["changeProduct"])
                self.deviceData[deviceId]["errorCode"]      = int(deviceData["errorCode"])

    def _connect_modbus(self):
        """
        Init MODBUS RTU connection
        """
        try:
            logging.error(self._configure)
            self._modbusMaster = ModbusSerialClient(
                method      = self._configure["METHOD"], 
                port        = self._configure["PORT"], 
                timeout     = self._configure["TIMEOUT"], 
                baudrate    = self._configure["BAUDRATE"]
            )
            self._modbusMaster.connect()
            self._modbusConnection = True
        except Exception as e:
            self._modbusConnection = False
            logging.error(str(e))

    def _save_raw_data_to_redis(self, topic, data):
        """
        Save raw data to redis
        """
        # logging.info(topic)
        for key in data.keys():
            self._redisClient.hset(topic,key ,data[key])

    def _parse_register_data(self,c,id1,id2):
        """
        Parse modbus data
        """
        a = c[id1]
        b = c[id2]
        s = struct.pack(">l", (b<<16)|a)
        return struct.unpack(">l", s)[0]

    def _start_reading_modbus(self):
        """
        Start reading modbus from device 
        """
        while self._kernelActive:
            if not self._modbusConnection:
                self._connect_modbus()
            else:
                for device in self._configure["LISTDEVICE"]:
                    deviceId                                = device["ID"]
                    self.deviceData[deviceId]["Device_id"]  = deviceId
                    rawTopic                                = deviceId + "/raw"
                    try:
                        # logging.critical(self._read_modbus_data)
                        self._read_modbus_data(device,deviceId)
                    except Exception as e:
                        logging.error(deviceId)
                        logging.error(str(e))
                        self.deviceData[deviceId]["status"] = STATUS.DISCONNECT
                    self._save_raw_data_to_redis(rawTopic,self.deviceData[deviceId])
            time.sleep(GeneralConfig.READINGRATE)

    def _read_modbus_data(self,device,deviceId):
        """
        Make request to read modbus and parse data 
        """
        r = self._modbusMaster.read_holding_registers(
            address = device["ADDRESS"], 
            count   = device["COUNT"], 
            unit    = device["UID"]
        )
        logging.warning(f"{device['ID']} --- {r}")
        registerData = r.registers
        
        status = 0
        if int(registerData[5]) == 1:
            status = STATUS.RUN
        elif int(registerData[5]) == 2:
            status = STATUS.IDLE
        else:
            status = STATUS.ERROR

        if int(registerData[5]) == 1:
            errorCode = 1
        else:
            errorCode = 0
        input           = int(registerData[1])
        output          = int(registerData[1])
        temperature     = float(registerData[5])
        humidity        = float(registerData[1])
        changeProduct   = int(registerData[11])
        self.deviceData[deviceId]["temperature"]    = temperature
        self.deviceData[deviceId]["humidity"]       = humidity
        statusChange    = self._is_status_change(deviceId,status)
        outputChange    = self._is_output_change(deviceId,output)
        inputChange     = self._is_input_change(deviceId, input)
        changingProduct = self._is_changing_product(deviceId,changeProduct)
        error           = self._is_error(deviceId,errorCode)
        # logging.warning(self.deviceData[deviceId])
        if statusChange or outputChange or changingProduct or inputChange or error:
            timeNow = int(float(VnTimeStamps.now()))
            self.deviceData[deviceId]["timestamp"]  = timeNow
            countRecords = MachineData.query.count()
            if countRecords > GeneralConfig.LIMITRECORDS:
                firstRecord = db.session.query(MachineData).first()
                db.session.query(MachineData).filter_by(id=firstRecord.id).delete()
                db.session.commit()
                db.session.close()
            insertData = MachineData(
                deviceId            = deviceId, 
                machineStatus       = status,
                output              = output,
                timestamp           = timeNow,
                humidity            = humidity,
                temperature         = temperature
                )
            try:
                db.session.add(insertData)
                db.session.commit()
                db.session.close() 
            except:
                db.session.rollback()
                db.session.close() 
            logging.error("Complete saving data!")

    def _is_status_change(self, deviceId, status):
        """
        Check if machine status change
        """
        if self.deviceData[deviceId]["status"] != status:
            logging.error(f"Status change, previous status: {self.deviceData[deviceId]['status']} - current status {status}")
            self.deviceData[deviceId]["status"] = status
            return True
        return False
        
    def _is_output_change(self, deviceId, output):
        """
        Check if output change
        """
        if self.deviceData[deviceId]["output"] != output:
            logging.error(f"output change, previous output: {self.deviceData[deviceId]['output']} - current output {output}")
            self.deviceData[deviceId]["output"] = output
            return True
        return False
    
    def _is_input_change(self, deviceId, input):
        """
        Check if input change
        """
        if self.deviceData[deviceId]["input"] != input:
            logging.error(f"input change, previous input: {self.deviceData[deviceId]['input']} - current input {input}")
            self.deviceData[deviceId]["input"] = input
            return True
        return False
    
    def _is_changing_product(self, deviceId, changeProduct):
        """
        Check if changing product
        """
        now = VnTimeStamps.now()
        if self.deviceData[deviceId]["changeProduct"] != changeProduct:
            logging.error("Stop changing product")
            self.deviceData[deviceId]["changeProduct"] = 0
            mqtt_client.publish(MQTTCnf.STARTPRODUCTION, json.dumps(self._generate_start_production_msg(deviceId, now)))
            return True

    def _is_error(self, deviceId, errorCode):
        """
        Check if error
        """
        if self.deviceData[deviceId]["errorCode"] != errorCode:
            logging.error(f"Error code change, previous errorCode: {self.deviceData[deviceId]['errorCode']} - current Error code {errorCode}")
            self.deviceData[deviceId]["errorCode"] = errorCode
            return True
        return False
    
    def _generate_start_production_msg(self, deviceId, now):
        return {
            "record_type"   : "tsl",
            "machine_id"    : deviceId,
            "timestamp"     : now
        }
