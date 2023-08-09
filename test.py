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
                    address = 4596, 
                    count   = 20, 
                    unit    = 4
                )
        # r1 = modbusMaster.read_holding_registers(
        #             address = 4624, 
        #             count   = 20, 
        #             unit    = 4
        #         )
        # r2 = modbusMaster.read_holding_registers(
        #             address = 4676, 
        #             count   = 20, 
        #             unit    = 4
        #         )
        print(r.registers)
        # print(r1.registers)
        # print(r2.registers)
        # time.sleep(0.5)
    except Exception as e:
        # logging.error(e) 
        time.sleep(1)
