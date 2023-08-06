from pymodbus.client.sync import ModbusSerialClient

from configure import STATUS

import logging
import struct

from ..utils import vntime as VnTimeStamps
from ..model.data_model import MachineData, UnsyncedMachineData



class BaseModbusPLC():
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
                    captured_data[device_id]["deviceId"]= device_id
                    
                    try:
                        captured_data = self._read_data(device, captured_data)
                        break
                    except Exception as e:
                        logging.error(e.__str__())
                        captured_data[device_id]["status"] = STATUS.DISCONNECT
        except Exception as e:
            logging.error(e.__str__())
        
        logging.debug("Captured: " + captured_data.__str__())

        return captured_data
    
    def _read_data(self,device:dict, captured_data:dict):
        """
        Make request to read modbus and parse data 
        """
        logging.debug("Execute _read_data()")
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

            # status and error code
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

            # parsing data
            input_data           = int(registerData[1])
            output_data          = int(registerData[1])
            temperature_data     = float(registerData[5])
            humidity_data        = float(registerData[1])
            changeProduct_data   = int(registerData[11])

            captured_data[device_id]["input"]         = input_data
            captured_data[device_id]["output"]         = output_data
            captured_data[device_id]["temperature"]    = temperature
            captured_data[device_id]["humidity"]       = humidity
            captured_data[device_id]["changeProduct"] = changeProduct_data
            captured_data[device_id]["status"]         = status
            captured_data[device_id]["error"]         = errorCode

        except Exception as e:
            logging.error("Fatal! " + e.__str__())
        return captured_data

    def _parse_register_data(self,c,id1,id2):
        """
        Parse modbus data
        """
        a = c[id1]
        b = c[id2]
        s = struct.pack(">l", (b<<16)|a)
        return struct.unpack(">l", s)[0]
