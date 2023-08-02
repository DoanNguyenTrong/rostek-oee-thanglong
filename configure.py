class ModbusCnf(object):
    SAVETIME    = 10 
    METHOD      = "rtu"
    PORT        = "/dev/ttyAMA4"
    COUNT       = 5
    TIMEOUT     = 1
    BAUDRATE    = 9600

class STATUS(object):
    DISCONNECT = 3
    RUN        = 1
    IDLE       = 0

class PLCCODE(object):
    NORMAL  = 0
    ERROR   = 1
class MQTTCnf(object):
    BROKER              = "103.1.237.18"
    PORT                = 1883
    PRODUCTIONTOPIC     = "/TLP/Sanluong"
    QUALITYTOPIC        = "/TLP/Chatluong"
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
    PORT    = 5103
    DEBUG   = True

deltaConfigure = {
        "METHOD"        :  "rtu",
        "PORT"          :  "/dev/ttyAMA4",
        "TIMEOUT"       :  1,
        "BAUDRATE"      :  9600,
        "LISTDEVICE"    : [            
            {
                "ID"        : "SN_UV",
                "UID"       : 1,
                "COUNT"     : 6,
                "ADDRESS"   : 4505,
            }
        ]
    }

deltaConfigure1 = {
        "METHOD"        :  "rtu",
        "PORT"          :  "/dev/ttyAMA3",
        "TIMEOUT"       :  1,
        "BAUDRATE"      :  9600,
        "LISTDEVICE"    : [            
            {
                "ID"        : "GL_637CIR",
                "UID"       : 1,
                "COUNT"     : 6,
                "ADDRESS"   : 4505,
            }
        ]
    }

deltaConfigure2 = {
        "METHOD"        :  "rtu",
        "PORT"          :  "/dev/ttyAMA2",
        "TIMEOUT"       :  1,
        "BAUDRATE"      :  9600,
        "LISTDEVICE"    : [            
            {
                "ID"        : "ACE70CS",
                "UID"       : 1,
                "COUNT"     : 6,
                "ADDRESS"   : 4505,
            }
        ]
    }
 
deltaConfigure3 = {
        "METHOD"        :  "rtu",
        "PORT"          :  "/dev/ttyAMA1",
        "TIMEOUT"       :  1,
        "BAUDRATE"      :  9600,
        "LISTDEVICE"    : [            
            {
                "ID"        : "MK1060MF",
                "UID"       : 1,
                "COUNT"     : 6,
                "ADDRESS"   : 4505,
            }
        ]
    }