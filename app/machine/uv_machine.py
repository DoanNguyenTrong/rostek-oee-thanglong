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
        r = self._modbusMaster.read_holding_registers(
            address = device["ADDRESS"], 
            count   = device["COUNT"], 
            unit    = device["UID"]
        )
        
        # logging.warning(f"{device['ID']} --- {r.registers}")
        registerData    = r.registers
        # logging.error(f"output - {r.registers[1]}")
        # logging.error(f"Status - {r.registers[5]}")
        # logging.error(f"ChangeProduct - {r.registers[11]}")
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

        input           = int(registerData[12])
        output          = int(registerData[4])
        changeProduct   = int(registerData[8])
        uv3             = int(registerData[20])
        uv2             = int(registerData[32])
        uv1             = int(registerData[44])

        self.deviceData[deviceId]["uv3"]  = uv3
        self.deviceData[deviceId]["uv2"]  = uv2
        self.deviceData[deviceId]["uv1"]  = uv1

        statusChange    = self._is_status_change(deviceId,status)
        outputChange    = self._is_output_change(deviceId,output)
        inputChange     = self._is_input_change(deviceId, input)
        changingProduct = self._is_changing_product(deviceId,changeProduct)
        error           = self._is_error(deviceId,errorCode)

        logging.warning(self.deviceData[deviceId])
        if statusChange or outputChange or changingProduct or inputChange or error:
            timeNow = int(float(VnTimeStamps.now()))
            self.deviceData[deviceId]["timestamp"]  = timeNow
            insertData = MachineData(
                deviceId            = deviceId,
                machineStatus       = status,
                output              = output,
                input               = input,
                runningNumber       = self.deviceData[deviceId]["runningNumber"],
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
                glueTemp            = -1,
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