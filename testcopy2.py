from pymodbus.client.sync import ModbusSerialClient
import logging, time

modbusMaster = ModbusSerialClient(
                method      = "rtu", 
                port        = "/dev/ttyAMA3", 
                timeout     = 1, 
                baudrate    = 9600
            )
modbusMaster.connect()
while True:
    try:
        logging.error("Trying")
        r = modbusMaster.read_holding_registers(
                    address = 4596, 
                    count   = 15, 
                    unit    = 1
                )
        r1 = modbusMaster.read_holding_registers(
                    address = 4246, 
                    count   = 15, 
                    unit    = 1
                )
        r2 = modbusMaster.read_holding_registers(
                    address = 4676, 
                    count   = 15, 
                    unit    = 1
                )
        print(r.registers)
        print(r1.registers)
        print(r2.registers)
        time.sleep(1)
    except Exception as e:
        # logging.error(e) 
        time.sleep(1)
