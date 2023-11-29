class ModbusCnf(object):
    SAVETIME    = 10 
    METHOD      = "rtu"
    PORT        = "/dev/ttyAMA4"
    COUNT       = 5
    TIMEOUT     = 1
    BAUDRATE    = 9600

class STATUS(object):
    DISCONNECT = 2
    RUN        = 1
    IDLE       = 0
    ERROR      = 1
    NORMAL     = 0

class MQTTCnf(object):
    BROKER              = "103.1.237.18"
    PORT                = 1883
    MQTT_USERNAME       = "ISIwwwTeam"
    MQTT_PASSWORD       = "123456"
    # BROKER              = "172.174.244.95"
    # PORT                = 1883
    # MQTT_USERNAME       = "rostek"
    # MQTT_PASSWORD       = "rostek2019"
    PRODUCTIONTOPIC     = "TLP/Sanluong"
    QUALITYTOPIC        = "TLP/Chatluong"
    STARTPRODUCTION     = "TLP/Tinhsanluong"
    TESTPRODUCTION      = "TLP/Thunghiem"
    MACHINETOPIC        = "TLP/Thietbi"
    RATETOPIC           = "/TLP/Fre"
    RECALLTOPIC         = "TLP/Recall"

    MQTT_KEEPALIVE      = 5
    MQTT_TLS_ENABLED    = False

class RedisCnf(object):
    HOST            = "localhost"
    PORT            = 6379
    PASSWORD        = ""
    RATETOPIC       = "/rate" 

class GeneralConfig(object):
    READINGRATE     = 0.5
    SENDINGRATE     = 1
    DEFAULTRATE     = 5
    LIMITRECORDS    = 70000
    DATAFILE        = "data.db"

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
                "UID"       : 3,
                "COUNT"     : 17,
                "ADDRESS"   : 4596,
                "ADDRESS1"  : 4616,
                "ADDRESS2"  : 4627,
                "COUNT1"    : 1,
                "COUNT2"    : 14,
            }
        ]
    }

printingMachineConfigure = {
        "METHOD"        :  "rtu",
        "PORT"          :  "/dev/ttyAMA3",
        "TIMEOUT"       :  1,
        "BAUDRATE"      :  9600,
        "LISTDEVICE"    : [            
            {
                "ID"        : "GL_637CIR",
                "UID"       : 1,
                "COUNT"     : 13,
                "COUNT1"    : 13,
                "COUNT2"    : 2,
                "ADDRESS"   : 4596,
                "ADDRESS1"  : 4676,
                "ADDRESS2"  : 4624,
            }
        ]
    }

boxFoldingMachineConfigure = {
        "METHOD"        :  "rtu",
        "PORT"          :  "/dev/ttyAMA1",
        "TIMEOUT"       :  1,
        "BAUDRATE"      :  9600,
        "LISTDEVICE"    : [            
            {
                "ID"        : "ACE70CS",
                "UID"       : 2,
                "COUNT"     : 17,
                "ADDRESS"   : 4596,
                "COUNT1"    : 13,
                "ADDRESS1"  : 4676,
                "ADDRESS2"  : 4624,
                "COUNT2"    : 1,
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
                "UID"       : 4,
                "COUNT"     : 17,
                "ADDRESS"   : 4596,
                "COUNT1"    : 4,
                "ADDRESS1"  : 4518,
            }
        ]
    }


listConfig = [uvMachineConfigure, printingMachineConfigure, boxFoldingMachineConfigure, cuttingMachineConfigure]
