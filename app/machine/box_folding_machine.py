from pymodbus.client.sync import ModbusSerialClient
import logging, json, struct, time
import utils.vntime as VnTimeStamps
from configure import *
from ..model.data_model import MachineData
from app import db
from .model_machine import MACHINE

class BOX_FOLDING_MACHINE(MACHINE):
    def _read_modbus_data(self,device,deviceId):
        """
        Make request to read modbus and parse data 
        """
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
        
        # logging.warning(f"{device['ID']} --- {r}")
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

        upperAirPressure    = int(registerData1[0])/10
        lowerAirPressure    = int(registerData1[4])/10
        gluePressure        = int(registerData1[8])/10
        glueTemp            = int(registerData1[12])/10

        input           = int(registerData2[0])
        output          = int(registerData[12])
        changeProduct   = int(registerData[8])

        self.deviceData[deviceId]["upperAirPressure"]   = upperAirPressure
        self.deviceData[deviceId]["lowerAirPressure"]   = lowerAirPressure
        self.deviceData[deviceId]["gluePressure"]       = gluePressure
        self.deviceData[deviceId]["glueTemp"]           = glueTemp

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
                upperAirPressure    = upperAirPressure,
                lowerAirPressure    = lowerAirPressure,
                gluePressure        = gluePressure,
                glueTemp            = glueTemp,
                isChanging          = changeProduct
                )
            try:
                db.session.add(insertData)
                db.session.commit()
                db.session.close() 
            except:
                db.session.rollback()
                db.session.close() 
            logging.error("Complete saving data!")  