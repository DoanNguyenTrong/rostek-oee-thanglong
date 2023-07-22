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

class GeneralConfig(object):
    READINGRATE = 5
    SENDINGRATE = 5

deltaConfigure = {
        "METHOD"        :  "rtu",
        "PORT"          :  "/dev/ttyAMA4",
        "TIMEOUT"       :  1,
        "BAUDRATE"      :  9600,
        "LISTDEVICE"    : [
            {
                "ID"        : "DVES_E94F2E",
                "UID"       : 2,
                "COUNT"     : 6,
                "ADDRESS"   : 4505,
            }
            ,
            {
                "ID"        : "DVES_E94F2C",
                "UID"       : 1,
                "COUNT"     : 6,
                "ADDRESS"   : 4505,
            }
        ]
    }
