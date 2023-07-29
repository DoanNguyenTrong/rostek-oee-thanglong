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
    BROKER              = "172.174.244.95"
    PORT                = 1883
    TOPIC               = "stat/V2/DVES_E94F2C/OEEDATA"
    MQTT_USERNAME       = "rostek"
    MQTT_PASSWORD       = "rostek2019"
    MQTT_KEEPALIVE      = 5
    MQTT_TLS_ENABLED    = False

class RedisCnf(object):
    HOST        = "localhost"
    PORT        = 6379
    PASSWORD    = ""
    SIEMENSINFO = "/info/siemens"
    DELTAINFO   = "/info/delta"
    HUMTEMPTOPIC= "/humtemp" 

class GeneralConfig(object):
    READINGRATE = 1
    SENDINGRATE = 1
    DEFAULTRATE = 5
    DATAFILE    = "data.db"

class FLASK(object):
    HOST    = '0.0.0.0'
    PORT    = 5103
    DEBUG   = True

deltaConfigure = {
        "METHOD"        :  "rtu",
        "PORT"          :  "/dev/ttyUSB0",
        "TIMEOUT"       :  1,
        "BAUDRATE"      :  9600,
        "LISTDEVICE"    : [
            {
                "ID"        : "DVES_E94F2H",
                "UID"       : 1,
                "COUNT"     : 12,
                "ADDRESS"   : 4505,
            }
            # ,
            # {
            #     "ID"        : "DVES_E94F2U",
            #     "UID"       : 1,
            #     "COUNT"     : 6,
            #     "ADDRESS"   : 4505,
            # }
        ]
    }
