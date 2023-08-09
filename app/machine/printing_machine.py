from pymodbus.client.sync import ModbusSerialClient
import logging, json, struct, time
import utils.vntime as VnTimeStamps
from configure import *
from ..model.data_model import MachineData
from app import db
from .model_machine import MACHINE

class PRINTING_MACHINE(MACHINE):
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
        
        # logging.warning(f"{device['ID']} --- {r.register}")
        # logging.warning(f"{device['ID']} --- {r1.register}")
        # logging.warning(f"{device['ID']} --- {r2.register}")
        registerData    = r.registers
        registerData1   = r1.registers
        registerData2   = r2.registers
        status = 0
        if int(registerData[0]) == 1:
            status = STATUS.RUN
        elif int(registerData[0]) == 2:
            status = STATUS.IDLE
        else:
            errorCode = 1

        if int(registerData[12]) == 0:
            errorCode = 0
        else:
            errorCode = 1
        envTemp         = int(registerData1[0])/10
        envHum          = int(registerData1[4])
        waterTemp       = int(registerData1[8])/10
        waterpH         = int(registerData1[12])/10
        input           = int(self._parse_register_data(registerData2, 0, 1))
        output          = int(self._parse_register_data(registerData, 4, 5))
        changeProduct   = int(registerData[8])
        # logging.error(changeProduct)

        self.deviceData[deviceId]["envTemp"]    = envTemp
        self.deviceData[deviceId]["envHum"]     = envHum
        self.deviceData[deviceId]["waterTemp"]  = waterTemp
        self.deviceData[deviceId]["waterpH"]    = waterpH

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
                envTemp             = envTemp,
                envHum              = envHum,
                waterTemp           = waterTemp,
                waterpH             = waterpH,
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
            logging.error("Complete saving data!")