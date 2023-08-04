class ModbusCnf(object):
    SAVETIME    = 10 
    METHOD      = "rtu"
    PORT        = "/dev/ttyAMA4"
    COUNT       = 5
    TIMEOUT     = 1
    BAUDRATE    = 9600

class STATUS(object):
    DISCONNECT = 0
    RUN        = 1
    IDLE       = 2
    ERROR      = 3

class MQTTCnf(object):
    BROKER              = "103.1.237.18"
    PORT                = 1883
    PRODUCTIONTOPIC     = "/TLP/Sanluong"
    QUALITYTOPIC        = "/TLP/Chatluong"
    STARTPRODUCTION     = "/TLP/Tinhsanluong"
    TESTPRODUCTION      = "/TLP/Thunghiem"
    MACHINETOPIC        = "/TLP/Thietbi"
    RATETOPIC           = "/TLP/Fre"
    RECALLTOPIC         = "/TLP/Recall"
    MQTT_USERNAME       = "ISIwwwTeam"
    MQTT_PASSWORD       = "123456"
    MQTT_KEEPALIVE      = 5
    MQTT_TLS_ENABLED    = False

class RedisCnf(object):
    HOST            = "localhost"
    PORT            = 6379
    PASSWORD        = ""
    RATETOPIC       = "/rate" 

class GeneralConfig(object):
    READINGRATE = 0.5
    SENDINGRATE = 1
    DEFAULTRATE = 5
    DATAFILE    = "data.db"

class FLASK(object):
    HOST    = '0.0.0.0'
    PORT    = 5104
    DEBUG   = True

uvMachineConfigure = {
        "METHOD"        :  "rtu",
        "PORT"          :  "/dev/ttyAMA4",
        "TIMEOUT"       :  1,
        "BAUDRATE"      :  9600,
        "LISTDEVICE"    : [            
            {
                "ID"        : "SN_UV",
                "UID"       : 1,
                "COUNT"     : 12,
                "ADDRESS"   : 4505,
            }
        ]
    }

printingMachineConfigure = {
        "METHOD"        :  "rtu",
        "PORT"          :  "/dev/ttyAMA4",
        "TIMEOUT"       :  1,
        "BAUDRATE"      :  9600,
        "LISTDEVICE"    : [            
            {
                "ID"        : "GL_637CIR",
                "UID"       : 1,
                "COUNT"     : 29,
                "COUNT1"    : 13,
                "ADDRESS"   : 4596,
                "ADDRESS1"  : 4676,
            }
        ]
    }

boxFoldingMachineConfigure = {
        "METHOD"        :  "rtu",
        "PORT"          :  "/dev/ttyAMA2",
        "TIMEOUT"       :  1,
        "BAUDRATE"      :  9600,
        "LISTDEVICE"    : [            
            {
                "ID"        : "ACE70CS",
                "UID"       : 1,
                "COUNT"     : 12,
                "ADDRESS"   : 4596,
                "COUNT1"    : 12,
                "ADDRESS1"  : 4676,
            }
        ]
    }
 
cuttingMachineConfigure = {
        "METHOD"        :  "rtu",
        "PORT"          :  "/dev/ttyAMA1",
        "TIMEOUT"       :  1,
        "BAUDRATE"      :  9600,
        "LISTDEVICE"    : [            
            {
                "ID"        : "MK1060MF",
                "UID"       : 1,
                "COUNT"     : 17,
                "ADDRESS"   : 4596,
            }
        ]
    }

listConfig = [uvMachineConfigure, printingMachineConfigure, boxFoldingMachineConfigure, cuttingMachineConfigure]