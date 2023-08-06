from pymodbus.client.sync import ModbusSerialClient

from configure import STATUS

import logging
from ..utils import vntime as VnTimeStamps
from ..model.data_model import MachineData, UnsyncedMachineData

from .base_modbus import BaseModbusPLC

class UvMachine(BaseModbusPLC):
    def _read_data(self,device:dict,captured_data:dict):
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
            input_data           = int(self._parse_register_data(r.registers, 12, 13))
            output_data          = int(self._parse_register_data(r.registers, 4, 5))
            changeProduct_data   = int(registerData[8])
            uv3_data             = int(registerData[20])
            uv2_data             = int(registerData[32])
            uv1_data             = int(registerData[44])

            captured_data[device_id]["input"]           = input_data
            captured_data[device_id]["output"]          = output_data
            captured_data[device_id]["changeProduct"]  = changeProduct_data
            captured_data[device_id]["uv3"]             = uv3_data
            captured_data[device_id]["uv2"]             = uv2_data
            captured_data[device_id]["uv1"]             = uv1_data
            captured_data[device_id]["status"]          = status
            captured_data[device_id]["errorCode"]       = errorCode
        
        except Exception as e:
            logging.error("Fatal! " + e.__str__())
        return captured_data
    

class BoxFolding(BaseModbusPLC):
    def _read_data(self,device:dict,captured_data:dict):
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
            input_data           = int(self._parse_register_data(r.registers, 12, 13))
            output_data          = int(self._parse_register_data(r.registers, 4, 5))
            changeProduct_data   = int(registerData[8])
            uv3_data             = int(registerData[20])
            uv2_data             = int(registerData[32])
            uv1_data             = int(registerData[44])

            captured_data[device_id]["input"]           = input_data
            captured_data[device_id]["output"]          = output_data
            captured_data[device_id]["changeProduct"]  = changeProduct_data
            captured_data[device_id]["uv3"]             = uv3_data
            captured_data[device_id]["uv2"]             = uv2_data
            captured_data[device_id]["uv1"]             = uv1_data
            captured_data[device_id]["status"]          = status
            captured_data[device_id]["errorCode"]       = errorCode
        
        except Exception as e:
            logging.error("Fatal! " + e.__str__())
        return captured_data