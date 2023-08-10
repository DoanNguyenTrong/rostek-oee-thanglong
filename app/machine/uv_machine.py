from pymodbus.client.sync import ModbusSerialClient
import logging, json, struct, time
import utils.vntime as VnTimeStamps
from configure import *
from ..model.data_model import MachineData
from .model_machine import MACHINE
from app import db

class UV_MACHINE(MACHINE):
    def _read_modbus_data(self,device,deviceId):
        """
        Make request to read modbus and parse data 
        """
        self._thisScan = VnTimeStamps.now()
        logging.critical(f"{deviceId}---{self._thisScan - self._lastScan}")
        self._lastScan = self._thisScan
        # logging.critical("Read here")
        r = self._modbusMaster.read_holding_registers(
            address = device["ADDRESS"], 
            count   = device["COUNT"], 
            unit    = device["UID"]
        )
        r1 = self._modbusMaster.read_holding_registers(
            address = device["ADDRESS1"], 
            count   = device["COUNT1"], 
            unit    = device["UID"]
        )
        r2 = self._modbusMaster.read_holding_registers(
            address = device["ADDRESS2"], 
            count   = device["COUNT2"], 
            unit    = device["UID"]
        )
        
        # logging.warning(f"{device['ID']} --- {r.registers}")
        # logging.warning(f"{device['ID']} --- {r1.registers}")
        # logging.warning(f"{device['ID']} --- {r2.registers}")
        registerData    = r.registers
        registerData1   = r1.registers
        registerData2   = r2.registers
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

        input           = int(self._parse_register_data(r.registers, 12, 13))
        output          = int(self._parse_register_data(r.registers, 4, 5))
        changeProduct   = int(registerData[8])
        uv3             = int(registerData1[0])
        uv2             = int(registerData2[1])
        uv1             = int(registerData2[13])

        self.deviceData[deviceId]["uv3"]  = uv3
        self.deviceData[deviceId]["uv2"]  = uv2
        self.deviceData[deviceId]["uv1"]  = uv1

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
                uv1                 = uv1,
                uv2                 = uv2,
                uv3                 = uv3,
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