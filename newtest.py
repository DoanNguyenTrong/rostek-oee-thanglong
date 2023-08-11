from pymodbus.client.sync import ModbusSerialClient
import logging, time

modbusMaster = ModbusSerialClient(
                method      = "rtu", 
                port        = "/dev/ttyAMA4", 
                timeout     = 1, 
                baudrate    = 9600
            )

modbusMaster.connect()
while True:
    try:
        logging.error("0 trying")
        r = modbusMaster.read_holding_registers(
                    address = 4596, 
                    count   = 17, 
                    unit    = 3
                )
    except:
        logging.error("0 error") 
    time.sleep(1)