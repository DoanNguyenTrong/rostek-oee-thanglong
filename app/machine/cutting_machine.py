from pymodbus.client.sync import ModbusSerialClient
import logging, json, struct, time
import utils.vntime as VnTimeStamps
from configure import *
from ..model.data_model import MachineData
from app import db
from .model_machine import MACHINE

class CUTTING_MACHINE(MACHINE):
    def _read_modbus_data(self,device,deviceId):
        """
        Make request to read modbus and parse data 
        """
        self._thisScan = VnTimeStamps.now()
        logging.info(f"{deviceId}---{self._thisScan - self._lastScan}")
        self._lastScan = self._thisScan
        r = self._modbusMaster.read_holding_registers(
            address = device["ADDRESS"], 
            count   = device["COUNT"], 
            unit    = device["UID"]
        )
        # logging.warning(f"{device['ID']} --- {r.registers}")
        registerData = r.registers
        status = 0 
        if int(registerData[0]) == 1:
            status = STATUS.RUN
        elif int(registerData[0]) == 0:
            status = STATUS.IDLE
        else:
            errorCode = 1

        if int(registerData[16]) == 0:
            errorCode = 0
        else:
            errorCode = 1

        input           = int(self._parse_register_data(registerData, 12, 13))
        output          = int(self._parse_register_data(registerData, 4, 5))
        changeProduct   = int(registerData[8])
        
        statusChange    = self._is_status_change(deviceId,status)
        outputChange    = self._is_output_change(deviceId,output)
        inputChange     = self._is_input_change(deviceId, input)
        changingProduct = self._is_changing_product(deviceId,changeProduct)
        error           = self._is_error(deviceId,errorCode)

        # logging.warning(self.deviceData[deviceId])
        if statusChange or outputChange or changingProduct or inputChange or error:
            timeNow = int(float(VnTimeStamps.now()))
            self.deviceData[deviceId]["timestamp"]  = timeNow
            insertData = MachineData(
                deviceId            = deviceId,
                machineStatus       = status,
                output              = output,
                input               = input,
                errorCode           = errorCode,
                envTemp             = -1,
                envHum              = -1,
                waterTemp           = -1,
                waterpH             = -1,
                timestamp           = timeNow,
                uv1                 = -1,
                uv2                 = -1,
                uv3                 = -1,
                upperAirPressure    = -1,
                lowerAirPressure    = -1,
                gluePressure        = -1,
                glueTemp            = -1
                )
            try:
                db.session.add(insertData)
                db.session.commit()
                db.session.close() 
            except:
                db.session.rollback()
                db.session.close() 
            logging.info("Complete saving data!")