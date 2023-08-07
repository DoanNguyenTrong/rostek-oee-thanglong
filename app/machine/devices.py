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
            reg = self.modbus_client.read_holding_registers(
                address = device["ADDRESS"], 
                count   = device["COUNT"], 
                unit    = device["UID"]
            )

            logging.debug(f"{device['ID']} --- {reg}")
            data_reg = reg.registers

            # status and error code
            if int(data_reg[5]) == 1:
                status = STATUS.RUN
            elif int(data_reg[5]) == 2:
                status = STATUS.IDLE
            else:
                status = STATUS.ERROR

            if int(data_reg[5]) == 1:
                errorCode = 1
            else:
                errorCode = 0

            # parsing data
            input_data           = int(self._parse_register_data(reg.registers, 12, 13))
            output_data          = int(self._parse_register_data(reg.registers, 4, 5))
            changeProduct_data   = int(data_reg[8])
            uv3_data             = int(data_reg[20])
            uv2_data             = int(data_reg[32])
            uv1_data             = int(data_reg[44])

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
    

class BoxFoldingMachine(BaseModbusPLC):
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
            reg_one = self.modbus_client.read_holding_registers(
            address = device["ADDRESS"], 
            count   = device["COUNT"], 
            unit    = device["UID"]
            )
            reg_two = self.modbus_client.read_holding_registers(
                address = device["ADDRESS1"], 
                count   = device["COUNT1"], 
                unit    = device["UID"]
            )
        
            logging.debug(f"{device['ID']} --- {reg_one}")
            logging.debug(f"{device['ID']} --- {reg_two}")
            data_reg_one = reg_one.registers
            data_reg_two = reg_two.registers

            status = STATUS.DISCONNECT
            errorCode = 0
            # status and error code
            if int(data_reg_one[0]) == 1:
                status = STATUS.RUN
            elif int(data_reg_one[0]) == 0:
                status = STATUS.IDLE
            else:
                errorCode = 1

            if int(data_reg_one[16]) == 0:
                errorCode = 0
            else:
                errorCode = 1
            
            
            input_data           = int(data_reg_one[28])
            output_data          = int(data_reg_one[12])
            product_change       = int(data_reg_one[8])
            # pasing data
            upperAirPressure    = int(data_reg_two[0])/10
            lowerAirPressure    = int(data_reg_two[4])/10
            gluePressure        = int(data_reg_two[8])/10
            glueTemp            = int(data_reg_two[12])/10

            captured_data[device_id]["status"] = status
            captured_data[device_id]["errorCode"] = errorCode
            
            captured_data[device_id]["input"] = input_data
            captured_data[device_id]["output"] = output_data
            captured_data[device_id]["changeProduct"] = product_change
            captured_data[device_id]["upperAirPressure"] = upperAirPressure
            captured_data[device_id]["lowerAirPressure"] = lowerAirPressure
            captured_data[device_id]["gluePressure"] = gluePressure
            captured_data[device_id]["glueTemp"] = glueTemp
        
        except Exception as e:
            logging.error("Fatal! " + e.__str__())
        return captured_data
    
class CuttingMachine(BaseModbusPLC):
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
            reg = self.modbus_client.read_holding_registers(
            address = device["ADDRESS"], 
            count   = device["COUNT"], 
            unit    = device["UID"]
            )
        
            logging.debug(f"{device['ID']} --- {reg}")
            data_reg = reg.registers

            status = STATUS.DISCONNECT
            errorCode = 0
            # status and error code
            if int(data_reg[0]) == 1:
                status = STATUS.RUN
            elif int(data_reg[0]) == 0:
                status = STATUS.IDLE
            else:
                errorCode = 1

            if int(data_reg[16]) == 0:
                errorCode = 0
            else:
                errorCode = 1
            
            
            input_data           = int(data_reg[12])
            output_data          = int(data_reg[4])
            product_changed       = int(data_reg[8])

            captured_data[device_id]["status"] = status
            captured_data[device_id]["errorCode"] = errorCode
            
            captured_data[device_id]["input"] = input_data
            captured_data[device_id]["output"] = output_data
            captured_data[device_id]["changeProduct"] = product_changed
        
        except Exception as e:
            logging.error("Fatal! " + e.__str__())
        return captured_data
    
class PrintingMachine(BaseModbusPLC):
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
            reg_one = self.modbus_client.read_holding_registers(
            address = device["ADDRESS"], 
            count   = device["COUNT"], 
            unit    = device["UID"]
            )
            reg_two = self.modbus_client.read_holding_registers(
                address = device["ADDRESS1"], 
                count   = device["COUNT1"], 
                unit    = device["UID"]
            )
        
            logging.debug(f"{device['ID']} --- {reg_one}")
            logging.debug(f"{device['ID']} --- {reg_two}")
            data_reg_one = reg_one.registers
            data_reg_two = reg_two.registers

            status = STATUS.DISCONNECT
            errorCode = 0
            # status and error code
            if int(data_reg_one[0]) == 1:
                status = STATUS.RUN
            elif int(data_reg_one[1]) ==2:
                status = STATUS.IDLE
            else:
                errorCode = 1

            if int(data_reg_one[12]) == 0:
                errorCode = 0
            else:
                errorCode = 1
            
            
            input_data           = int(data_reg_one[28])
            output_data          = int(data_reg_one[12])
            product_change       = int(data_reg_one[8])
            # pasing data
            envTemp         = int(data_reg_two[0])/10
            envHum          = int(data_reg_two[4])/10
            waterTemp       = int(data_reg_two[8])/10
            waterpH         = int(data_reg_two[12])/10

            captured_data[device_id]["status"] = status
            captured_data[device_id]["errorCode"] = errorCode
            
            captured_data[device_id]["input"] = input_data
            captured_data[device_id]["output"] = output_data
            captured_data[device_id]["changeProduct"] = product_change

            captured_data[device_id]["envTemp"] = envTemp
            captured_data[device_id]["envHum"] = envHum
            captured_data[device_id]["waterTemp"] = waterTemp
            captured_data[device_id]["waterpH"] = waterpH
        
        except Exception as e:
            logging.error("Fatal! " + e.__str__())
        return captured_data