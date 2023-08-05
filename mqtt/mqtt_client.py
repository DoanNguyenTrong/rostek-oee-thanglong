import logging, time
import numpy as np
import paho.mqtt.client as mqtt

from .handle_message import *


def mqtt_args_parser(parser):
    """Add parser augument for MQTT options."""
    parser.add_argument('--name', type=str, default=None,
                        help='name of client')
    parser.add_argument('--ip', type=str, default=None,
                        help='broker\'s ip, e.g., 192.168.0.1')
    parser.add_argument('--pub', type=str, default=None,
                        help='topic to be published')
    parser.add_argument('--sub', type=str, default=None,
                        help='topic to be subscribed')
    parser.add_argument('--freq', type=int, default=60,
                        help='Data recording frequency')
    parser.add_argument('--sensor_type', type=str, default=None,
                        help='Type of the sensor')
    return parser

def mqtt_args_json(args, configs):
    """
        Load configuration params for mqtt objects
    """
    if "name" in configs and not configs["name"] == "None":
        logging.info("name: %s" %configs["name"])
        args.name = configs["name"]   
    if "ip" in configs and not configs["ip"] == "None":
        logging.info("ip: %s" %configs["ip"])
        args.ip = configs["ip"]
    if "pub" in configs and not configs["pub"] == "None":
        logging.info("pub: %s" %configs["pub"])
        args.pub = configs["pub"]
    if "sub" in configs and not configs["sub"] == "None":
        logging.info("sub: %s" %configs["sub"])
        args.sub = configs["sub"]
    if "freq" in configs and not configs["freq"] == 0:
        logging.info("freq: %s" %str(configs["freq"]))
        args.freq = configs["freq"]
    if "sensor_type" in configs and not configs["sensor_type"] == 'None':
        logging.info("sensor_type: %s" %str(configs["sensor_type"]))
        args.sensor_type = configs["sensor_type"]
    return args

def on_connect(client, userdata, flags, rc):
    """Callback function when a connection is establised"""
    if rc==0:
        client.connected_flag=True #set flag
        client.reconnecting_flag    = False # TODO: unknown
        logging.info("Connected OK Returned code: %s \n"%rc)
        #client.subscribe(topic)
    else:
        logging.info("Bad connection Returned code: %s \n"%rc)

def on_disconnect(client, userdata, rc):
    """Callback function when disconnection"""

    logging.info("Disconnecting reason %s " % str(rc))
    client.connected_flag=False
    client.disconnect_flag=True

def on_message(client, userdata, message):
    """
        Callback function when client is a CO2 publisher
        print out the received message
        check FLAG and perform mode switching
    """
    received_data    = json.loads(str(message.payload.decode("utf-8")))
    message_topic   = str(message.topic)
    deviceId = str(message_topic.split("/")[2]) 
    logging.info("Topic: {}, msg: {}, retained: {}".format(message_topic, \
                                                           message.payload.decode("utf-8"), \
                                                           message.retain))
    if "/humtemprate" in message_topic:
        redisClient = userdata["redisClient"]
        handle_humtemp_rate_data(client,received_data,redisClient)
    elif "/requestData" in message_topic:
        redisClient = userdata["redisClient"]
        handle_request_data(deviceId,received_data,client)
    
    if message.retain==1:
        logging.debug("This is a retained message")



def on_publish(client,userdata,result):
    """Callback if a message is publised"""
    logging.info("data published \n")

def on_log(client, userdata, level, buf):
    """
    Troubleshoot using Logging
    """
    logging.info("MQTTClient log: ",buf)


class MQTTClient():
    def __init__(self, broker_ip:str, broker_port:str, client_name:str, data:dict, credential = None):
        self.broker_ip = broker_ip
        self.broker_port = broker_port
        self.client_name = client_name
        
        self.username = None
        self.password = None

        self.client = mqtt.Client(client_name, userdata=data)
        
        # callback functions
        self.client.on_publish    = on_publish
        self.client.on_connect    = on_connect
        self.client.on_disconnect = on_disconnect
        self.client.on_message = on_message
        #self.client.on_log        = on_log
        # username and password
        if not credential == None:
            logging.info( "Login a network with credential verification" )
            self.client.username_pw_set(username=credential[0],password=credential[1])
        
    
    def connect(self, keep_alive, username, password, sleeptime=2):
        """Connect to broker:port"""
        logging.info("Connecting to broker {}:{}".format(self.broker_ip,self.broker_port))
        try:
            self.client.connect(self.broker_ip, port=self.broker_port, keepalive=keep_alive) #connect to broker
            self.client.username_pw_set(username=username, password=password)
            self.username = username
            self.password = password
            self.keepalive = keep_alive
            time.sleep(sleeptime) # Wait for connection setup to complete
        except Exception as e:
            logging.error(e.__str__())
    
    def subscribe(self, topics:list):
        """Subscribe to "topic" """
        logging.info('subscribing to topic %s' % topic)
        try:
            for topic in topics:
                if isinstance(topic, str):
                    self.client.subscribe(topic)
                else:
                    logging.error(f"Unknown topic: {topic}")
        except Exception as e:
            logging.error(e.__str__())

    def publish(self, topic, data, qos = 1, retain=False):
        """Publish "data" -> "topic" """

        logging.info("Publishing message to topic %s" % topic)
        
        self.client.publish(topic, data, qos=qos, retain=retain)
    
    def reconnect(self):
        logging.debug("Reconnecting....")
        self.connect(self.keepalive, self.username, self.password)

    def data_concatenate(self, data):
        """ Concatenate "data" into a single string
            Add timestamp and "client_name"
            Ready for publish
        """
        data_str = ''
        for st in data:
            data_str += str(st) + ','
        
        data_str += '\'' + time.strftime('%Y-%m-%d-%H-%M-%S', time.localtime()) + '\''
        data_str += ',' + '\'' + self.client_name + '\''
        data_str += ',' + '\'' + self.sensor_type + '\''
        return data_str
    
