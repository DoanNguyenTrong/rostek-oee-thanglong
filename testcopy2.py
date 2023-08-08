from pymodbus.client.sync import ModbusSerialClient
import logging, time

modbusMaster = ModbusSerialClient(
                method      = "rtu", 
                port        = "/dev/ttyAMA1", 
                timeout     = 1, 
                baudrate    = 9600
            )
modbusMaster.connect()
while True:
    try:
        logging.error("Trying")
        r = modbusMaster.read_holding_registers(
                    address = 4616, 
                    count   = 1, 
                    unit    = 2
                )
        print(r.registers)
        time.sleep(1)
    except Exception as e:
        # logging.error(e) 
        time.sleep(1)
