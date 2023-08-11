# from pymodbus.client.sync import ModbusSerialClient
# import logging, time




# while True:
#     try:
#         modbusMaster = ModbusSerialClient(
#                 method      = "rtu", 
#                 port        = "/dev/ttyAMA1", 
#                 timeout     = 1, 
#                 baudrate    = 9600
#             )
#         modbusMaster.connect()
#         logging.error("Trying ")
#         r = modbusMaster.read_holding_registers(
#                     address = 4596, 
#                     count   = 20, 
#                     unit    = 4
#                 )
#         print(r.registers)
#     except:
#         logging.error("failed ")
#     try:
#         modbusMaster1 = ModbusSerialClient(
#                 method      = "rtu", 
#                 port        = "/dev/ttyAMA4", 
#                 timeout     = 1, 
#                 baudrate    = 9600
#             )
#         modbusMaster1.connect()
#         logging.error("Trying 1")
#         r1 = modbusMaster1.read_holding_registers(
#                     address = 4624, 
#                     count   = 20, 
#                     unit    = 3
#                 )
#         print(r1.registers)
#     except:
#         logging.error("failed-1")
#     try:
#         modbusMaster2 = ModbusSerialClient(
#                 method      = "rtu", 
#                 port        = "/dev/ttyAMA3", 
#                 timeout     = 1, 
#                 baudrate    = 9600
#             )
#         modbusMaster2.connect()
#         logging.error("Trying 2")
#         r2 = modbusMaster2.read_holding_registers(
#                     address = 4676, 
#                     count   = 20, 
#                     unit    = 1
#                 )
#         print(r2.registers)
#     except: 
#         logging.error("failed-2")
#     time.sleep(1)

from pymodbus.client.sync import ModbusSerialClient
import logging, time

modbusMaster = ModbusSerialClient(
                method      = "rtu", 
                port        = "/dev/ttyAMA0", 
                timeout     = 1, 
                baudrate    = 9600
            )
modbusMaster1 = ModbusSerialClient(
                method      = "rtu", 
                port        = "/dev/ttyAMA1", 
                timeout     = 1, 
                baudrate    = 9600
            )
modbusMaster2 = ModbusSerialClient(
                method      = "rtu", 
                port        = "/dev/ttyAMA2", 
                timeout     = 1, 
                baudrate    = 9600
            )
modbusMaster3 = ModbusSerialClient(
                method      = "rtu", 
                port        = "/dev/ttyAMA3", 
                timeout     = 1, 
                baudrate    = 9600
            )
modbusMaster4 = ModbusSerialClient(
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
                    unit    = 2
                )
        logging.error(r.registers)
    except:
        logging.error("0 error") 
    try:
        logging.error("1 trying")
        r = modbusMaster1.read_holding_registers(
                    address = 4596, 
                    count   = 17, 
                    unit    = 2
                )
        logging.error(r.registers)
    except:
        logging.error("1 error") 
    try:
        logging.error("2 trying")
        r = modbusMaster2.read_holding_registers(
                    address = 4596, 
                    count   = 17, 
                    unit    = 2
                )
        logging.error(r.registers)
    except:
        logging.error("2 error") 
    try:
        logging.error("3 trying")
        r = modbusMaster3.read_holding_registers(
                    address = 4596, 
                    count   = 17, 
                    unit    = 2
                )
        logging.error(r.registers)
    except:
        logging.error("3 error") 
    try:
        logging.error("4 trying")
        r = modbusMaster4.read_holding_registers(
                    address = 4596, 
                    count   = 17, 
                    unit    = 2
                )
        logging.error(r.registers)
    except:
        logging.error("4 error") 
    time.sleep(0.5)