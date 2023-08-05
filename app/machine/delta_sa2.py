from pymodbus.client.sync import ModbusSerialClient

from configure import STATUS

import logging
from ..utils import vntime as VnTimeStamps
from ..model.data_model import MachineData, UnsyncedMachineData



class DELTA_SA2_Modbus():
    def __init__(self, configure:dict) -> None:
        self.configure = configure
        self.modbus_client = None
        self.modbus_connected = False
        self.__connect_modbus()

    def __connect_modbus(self):
        """
        Init MODBUS RTU connection
        """
        try:
            logging.critical("Modbus Configuration: "+ self.configure.__str__())
            logging.critical("Connecting to modbus: method: {},port:{}, timeout: {}, baudrate: {}".format(
                self.configure["METHOD"],
                self.configure["PORT"],
                self.configure["TIMEOUT"],
                self.configure["BAUDRATE"]
            ))

            self.modbus_client = ModbusSerialClient(
                method      = self.configure["METHOD"], 
                port        = self.configure["PORT"], 
                timeout     = self.configure["TIMEOUT"], 
                baudrate    = self.configure["BAUDRATE"]
            )
            self.modbus_client.connect()

            self.modbus_connected = True
        except Exception as e:
            self.modbus_connected = False
            logging.error("Fatal "+e.__str__())
        finally:
            logging.info("Successfully connected!")
    
    def read_modbus(self, captured_data:dict) -> dict:
        """
        Start reading modbus from device 
        """
        logging.debug("Execute: read_modbus()")
        try:
            if not self.modbus_connected:
                self.__connect_modbus()
            else:
                for device in self.configure["LISTDEVICE"]:
                    device_id = device["ID"]
                    captured_data[device_id]= {}
                    captured_data[device_id]["Device_id"]= device_id
                    
                    try:
                        captured_data = self.__read_data(device, captured_data)
                        break
                    except Exception as e:
                        logging.error(e.__str__())
                        captured_data[device_id]["status"] = STATUS.DISCONNECT
        except Exception as e:
            logging.error(e.__str__())
        
        logging.debug("Captured: " + captured_data.__str__())

        return captured_data
    
    def __read_data(self,device:dict, captured_data:dict):
        """
        Make request to read modbus and parse data 
        """
        logging.debug("Execute __read_data()")
        try:
            logging.debug("Reading! id: {}, address:{}, count:{}, uid:{}".format(device["ID"],
                                                                                 device["ADDRESS"],
                                                                                 device["COUNT"], 
                                                                                 device["UID"]))
            device_id = device["ID"]
            r = self.modbus_client.read_holding_registers(
                address = device["ADDRESS"], 
                count   = device["COUNT"], 
                unit    = device["UID"]
            )

            logging.debug(f"{device['ID']} --- {r}")
            registerData = r.registers
            logging.debug(f"Actual - {r.registers[1]}")
            logging.debug(f"Status - {r.registers[5]}")
            logging.debug(f"ChangeProduct - {r.registers[11]}")

            if int(registerData[5]) == 1:
                status = STATUS.RUN
            elif int(registerData[5]) == 2:
                status = STATUS.IDLE
            else:
                status = STATUS.ERROR

            actual          = int(registerData[1])
            temperature     = float(registerData[5]) # 
            humidity        = float(registerData[1]) # Fake
            changeProduct   = int(registerData[11])

            captured_data[device_id]["temperature"]    = temperature
            captured_data[device_id]["humidity"]       = humidity
            captured_data[device_id]["change_product"] = changeProduct
            captured_data[device_id]["actual"]         = actual
            captured_data[device_id]["status"]         = status
        except Exception as e:
            logging.error("Fatal! " + e.__str__())
        return captured_data
    
class RedisMonitor():
    def __init__(self, redis_client, sql_database_client, configure) -> None:
        self.configure = configure
        self.redis_client = redis_client
        self.sql_database_client = sql_database_client

    def get_redis_data(self, topic):
        """
        Load old data from redis
        """
        latest_data = dict()
        logging.debug("Execute: get_redis_data()")

        for device in self.configure["LISTDEVICE"]:
            device_id    = device["ID"]
            # rawTopic    = "/device/V2/" + device["ID"] + "/raw"
            # TODO: why read all, can be the latest only?
            logging.debug(f"Query Redis topic:{topic}")
            redis_data  = self.redis_client.hgetall(topic)

            latest_data[device_id]               = {}
            latest_data[device_id]["timestamp"]  = int(float(VnTimeStamps.now()))
            
            if "runningNumber" not in redis_data:
                latest_data[device_id]["runningNumber"]  = 0
                latest_data[device_id]["status"]         = STATUS.DISCONNECT
                latest_data[device_id]["actual"]         = 0
                latest_data[device_id]["ng"]             = 0
                latest_data[device_id]["changeProduct"]  = 0
            else:
                latest_data[device_id]["runningNumber"]  = int(redis_data["runningNumber"]) 
                latest_data[device_id]["status"]         = int(redis_data["status"]) 
                latest_data[device_id]["actual"]         = int(redis_data["actual"]) 
                latest_data[device_id]["ng"]             = int(redis_data["ng"]) 
                latest_data[device_id]["changeProduct"]  = int(redis_data["changeProduct"])
        logging.debug(f"Redis data: {latest_data}")
        return latest_data
    
    def compare_and_save(self, device_id, redis_data:dict, current_data:dict):
        
        status_changed    = self.__is_status_change(redis_data,current_data["status"])
        actual_changed    = self.__is_actual_change(redis_data, current_data["actual"])
        product_changed = self.__is_changing_product(redis_data, current_data["changeProduct"])
    
        if status_changed or actual_changed or product_changed:
            timeNow = int(float(VnTimeStamps.now()))
            current_data["timestamp"]  = timeNow
            data = MachineData(
                device_id            = device_id, 
                machineStatus       = current_data['status'],
                actual              = current_data['actual'],
                timestamp           = timeNow,
                humidity            = current_data['humidity'],
                runningNumber       = current_data["runningNumber"],
                temperature         = current_data['temperature'],
                isChanging          = current_data['changeProduct']
                )
            unsynced_data = UnsyncedMachineData(
                device_id            = device_id, 
                machineStatus       = current_data['status'],
                actual              = current_data['actual'],
                timestamp           = timeNow,
                humidity            = current_data['humidity'],
                runningNumber       = current_data["runningNumber"],
                temperature         = current_data['temperature'],
                isChanging          = current_data['changeProduct']
                )
        self.save_to_sql(data, unsynced_data)
    
    def save_to_sql(self, data, unsynced_data):    
        try:
            self.sql_database_client.session.add(data)
            self.sql_database_client.session.add(unsynced_data)
            self.sql_database_client.session.commit()
            self.sql_database_client.session.close() 
        except Exception as e:
            self.sql_database_client.session.rollback()
            self.sql_database_client.session.close() 
            logging.error(e.__str__())
        logging.debug("Complete saving data!")

    def __is_status_change(self, data:dict, status):
        """
        Check if machine status change
        """
        if data["status"] != status:
            logging.debug(f"Status change, prev: {data['status']} - cur: {status}")
            # data["status"] = status
            return True
        return False
        
    def __is_actual_change(self, data:dict, actual):
        """
        Check if actual change
        """
        if data["actual"] != actual:
            logging.debug(f"Status change, prev: {data['actual']} - cur: {actual}")
            # data["actual"] = actual
            return True
        return False
    
    def __is_changing_product(self, data:dict, changeProduct):
        """
        Check if changing product
        """

        # TODO: need to be concatenated!
        now = VnTimeStamps.now()
        if data["changeProduct"] == 0 and changeProduct == 1:
            logging.debug(f"Start changing product, prev: {data['runningNumber']}, curr: {changeProduct}")
            # data["changeProduct"] = changeProduct
            return True
        elif data["changeProduct"] == 1 and changeProduct == 0:
            # data["runningNumber"] += 1
            logging.debug(f"Stop changing product, cur: {data['changeProduct']}, curr: {changeProduct}")
            # data["changeProduct"] = changeProduct
            return True
        else:
            return False
