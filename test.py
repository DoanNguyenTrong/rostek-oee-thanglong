from pymodbus.client.sync import ModbusSerialClient
import logging, time




while True:
    try:
        modbusMaster = ModbusSerialClient(
                method      = "rtu", 
                port        = "/dev/ttyAMA1", 
                timeout     = 1, 
                baudrate    = 9600
            )
        modbusMaster.connect()
        logging.error("Trying ")
        r = modbusMaster.read_holding_registers(
                    address = 4596, 
                    count   = 20, 
                    unit    = 4
                )
        print(r.registers)
    except:
        logging.error("failed ")
    try:
        modbusMaster1 = ModbusSerialClient(
                method      = "rtu", 
                port        = "/dev/ttyAMA4", 
                timeout     = 1, 
                baudrate    = 9600
            )
        modbusMaster1.connect()
        logging.error("Trying 1")
        r1 = modbusMaster1.read_holding_registers(
                    address = 4624, 
                    count   = 20, 
                    unit    = 3
                )
        print(r1.registers)
    except:
        logging.error("failed-1")
    try:
        modbusMaster2 = ModbusSerialClient(
                method      = "rtu", 
                port        = "/dev/ttyAMA3", 
                timeout     = 1, 
                baudrate    = 9600
            )
        modbusMaster2.connect()
        logging.error("Trying 2")
        r2 = modbusMaster2.read_holding_registers(
                    address = 4676, 
                    count   = 20, 
                    unit    = 1
                )
        print(r2.registers)
    except: 
        logging.error("failed-2")
    time.sleep(1)