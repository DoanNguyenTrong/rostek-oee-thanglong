import logging, time
import paho.mqtt.client as mqtt
import json

from configure import MQTTCnf, RedisCnf

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



class MQTTClient():
    __instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance
    
    def __init__(self, configures:MQTTCnf, user_data:dict, credential = None):
        self.configures = configures
        self.user_data = user_data

        self.keepalive = False

        self.client = mqtt.Client(self.configures.BROKER_IP, userdata=user_data, clean_session=False, reconnect_on_failure=True)
        self.client.username_pw_set(username=self.configures.MQTT_USERNAME, 
                                        password=self.configures.MQTT_PASSWORD)
        
        self.subscribe_topic = []  # Store the topic for re-subscription

        #self.client.on_log        = on_log
        
        # # username and password
        # if not credential == None:
        #     logging.info( "Login a network with credential verification" )
        #     try:
        #         self.client.username_pw_set(username=credential[0],password=credential[1])
        #     except Exception as e:
        #         logging.error(e.__str__())
        #         logging.error(f"Credential: {credential}")
    
    def connect(self, keep_alive=True, sleeptime=2):
        """Connect to broker:port"""
        logging.info("Connecting to broker {}:{}".format(self.configures.BROKER_IP,
                                                         self.configures.PORT))
        try:
            self.client.connect(self.configures.BROKER_IP, 
                                port=self.configures.PORT, 
                                keepalive=keep_alive) #connect to broker
            
            self.keepalive = keep_alive
            
            # callback functions
            self.client.on_publish = self.on_publish
            self.client.on_message = self.on_message
            self.client.on_subscribe = self.on_subscribe
            self.client.on_disconnect = self.on_disconnect
            self.client.on_log = self.on_log

            self.client.loop_start()
            time.sleep(sleeptime) # Wait for connection setup to complete
        except Exception as e:
            logging.error(e.__str__())
    
    def subscribe(self, topics:list, QoS=2):
        """Subscribe to "topic" """
        try:
            for topic in topics:
                if isinstance(topic, str):
                    logging.info(f'Subscribing to topic {topic}')
                    self.client.subscribe(topic=topic, qos=QoS)
                    
                    # add new topic to list of subscribe topics
                    if topic not in self.subscribe_topic:
                        self.subscribe_topic.append(topic)

                else:
                    logging.error(f"Unknown topic: {topic}")
        except Exception as e:
            logging.error(e.__str__())

    def publish(self, topic, data, qos = 1, retain=False):
        """Publish "data" -> "topic" """

        logging.debug("Publishing message to topic %s" % topic)
        self.user_data['topic'] = topic
        self.client.user_data_set(self.user_data)
        result, mid = self.client.publish(topic, data, qos=qos, retain=retain)
        # logging.debug(f"Result:{result}")
        # logging.debug(f"Result:{mid}")
        if result != 0:
            logging.error(f'Failed to send, rc: {result}')
    
    
    def disconnect(self):
        logging.debug("Disconnecting...........")
        self.client.loop_stop()
        self.client.disconnect()

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

    def on_connect(self, client, userdata, flags, rc):
        """Callback function when a connection is establised"""
        if rc==0:
            self.client.connected_flag=True #set flag
            self.client.reconnecting_flag    = False # TODO: unknown
            logging.info("Connected OK Returned code: %s \n"%rc)
            logging.critical(f'Subscribing to topic /TLP/Fre')
            self.client.subscribe("/TLP/Fre")
        else:
            logging.info("Bad connection Returned code: %s \n"%rc)

    def on_subscribe(self, client, userdata, mid, granted_qos):
        logging.critical(f"Subscribed to topic with MID:{mid}, {granted_qos}")

    def on_disconnect(self, client, userdata, rc):
        """Callback function when disconnection"""

        logging.error("Disconnecting reason %s " % str(rc))
        self.client.connected_flag=False
        self.client.disconnect_flag=True
        
        # if rc != 0:
        #     logging.critical("Disconnected unexpectedly. Reconnecting...")
        #     self.disconnect()
        #     time.sleep(5)
        #     self.connect(keep_alive=self.keepalive)
        #     if self.subscribe_topic:
        #         self.subscribe(self.subscribe_topic)

    def on_message(self, client, userdata, message):
        """
            Callback function when client is a CO2 publisher
            print out the received message
            check FLAG and perform mode switching
        """
        received_data    = json.loads(str(message.payload.decode("utf-8")))
        message_topic   = str(message.topic)
        deviceId = str(message_topic.split("/")[2]) 

        topic   = str(message.topic)
        deviceId = str(topic.split("/")[2])
        logging.critical("Topic: {}, msg: {}, retained: {}".format(message_topic, \
                                                            message.payload.decode("utf-8"), \
                                                            message.retain))
        if "/TLP/Fre" in topic:
            recordType = received_data["record_type"]
            redisClient = userdata["redisClient"]
            logging.debug(f"Receive control command to topic:{topic}, data: {received_data}")
            if recordType == "sx":
                freq = received_data["frequency"]
                redisClient.hset(RedisCnf.RATETOPIC, "production", freq)
                logging.critical(f"Change production freq to {freq}")
            elif recordType == "cl":
                redisClient.hset(RedisCnf.RATETOPIC, "quality", received_data["frequency"])
                logging.critical("Change quality freq")
            elif recordType == "tb":
                redisClient.hset(RedisCnf.RATETOPIC, "machine", received_data["frequency"])
                logging.critical("Change machine freq")

        elif "/requestData" in topic:
            redisClient = userdata["redisClient"]
            # handle_request_data(deviceId,received_data,client)
        elif "/humtemprate" in message_topic:
            redisClient = userdata["redisClient"]
            # handle_humtemp_rate_data(client,received_data,redisClient)
        elif "/requestData" in message_topic:
            redisClient = userdata["redisClient"]
            # handle_request_data(deviceId,received_data,client)
        
        if message.retain==1:
            logging.debug("This is a retained message")

    def on_publish(self, client,userdata,result):
        """Callback if a message is publised"""
        logging.debug(f"Message published with result:{result}")
        logging.debug(f"data published to {userdata['topic']}\n")

    def on_log(self, client, userdata, level, buf):
        """
        Troubleshoot using Logging
        """
        logging.info(f"MQTTClient log: {buf}")