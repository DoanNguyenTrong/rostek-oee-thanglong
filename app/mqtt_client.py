import logging, time
import paho.mqtt.client as mqtt
import json

from configure import MQTTCnf, RedisCnf
from sqlalchemy import and_


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
    
    def connect(self, keep_alive=True, sleeptime=2, log_enable=False):
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
            
            if log_enable:
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

    def add_userdata(self, key:str, data_obj, print_data=True):
        self.user_data[key] = data_obj
        if print_data:
            logging.critical("MQTT DATA")
            logging.critical(self.user_data)

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
            logging.critical(f'Subscribing to topic TLP/Recall')
            logging.critical(f'Subscribing to topic /TLP/Fre')
            # topics = [("/TLP/Fre", 2), ("TLP/Recall", 2)]
            topics = [("/TLP/Fre", 2)]
            self.client.subscribe(topics)
            self.client.subscribe('TLP/Recall', 2)


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

        topic   = str(message.topic)
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

        elif "/TLP/Recall" in topic:
            sql_model = userdata["sql_model"]
            
            timeFrom    = received_data["from"]
            timeTo      = received_data["to"]
            record_type = received_data["record_type"]
            machine_id = received_data["machine_id"]

            logging.critical(f"Data being requested from {timeFrom}, to {timeTo}")


            results = sql_model.query.filter(and_(sql_model.timestamp >= timeFrom,
                                                  sql_model.timestamp <= timeTo, 
                                                  sql_model.deviceId == machine_id)).all()
            logging.critical(f"Raw data {results}")
            data = []
            to_topic = ''
            if 'sx' in record_type:
                to_topic = MQTTCnf.PRODUCTIONTOPIC
                
                for result in results:
                    logging.critical(f"Querried data: {result}")
                    production_data = {
                            "record_type"   : "sx",
                            "input"         : result["input"]       if "input"    in result else -1,
                            "output"        : result["output"]      if "output"   in result else -1,
                            "machine_id"    : result["deviceId"]    if "deviceId"   in result else -1,
                            "timestamp"     : result['timestamp']    if "timestamp"   in result else -1,
                        }
                    
                    data.append(production_data)
                    
            elif 'cl' in record_type:
                to_topic = MQTTCnf.QUALITYTOPIC
                
                for result in results:
                    logging.critical(f"Querried data: {result}")
                    quality_data = {
                            "record_type"   : "cl",
                            "w_temp"        : result["waterTemp"] if "waterTemp"  in result else -1,
                            "ph"            : result["waterpH"]   if "waterpH"    in result else -1,
                            "t_ev"          : result["envTemp"]   if "envTemp"    in result else -1,
                            "e_hum"         : result["envHum"]    if "envHum"     in result else -1,
                            "uv1"           : result["uv1"]       if "uv1"        in result else -1,
                            "uv2"           : result["uv2"]       if "uv2"        in result else -1,
                            "uv3"           : result["uv3"]       if "uv3"        in result else -1,
                            "p_cut"         : result["p_cut"]     if "p_cut"      in result else -1,
                            "p_conv1"       : result["p_conv"]    if "p_conv"     in result else -1,
                            "p_conv2"       : result["p_conv"]    if "p_conv"     in result else -1,
                            "p_gun"         : result["p_gun"]     if "p_gun"      in result else -1,
                            "machine_id"    : result["deviceId"]    if "deviceId"   in result else -1,
                            "timestamp"     : result['timestamp']    if "timestamp"   in result else -1,
                        }
                    
                    data.append(quality_data)
            elif 'tb' in record_type:
                to_topic = MQTTCnf.MACHINETOPIC
                
                for result in results:
                    logging.critical(f"Querried data: {result}")
                    machine_data = {
                            "record_type"   : "cl",
                            "status"        : result["status"] if "status"  in result else -1,
                            "type"            : result["errorCode"]   if "errorCode"    in result else -1,
                            "machine_id"    : result["deviceId"]    if "deviceId"   in result else -1,
                            "timestamp"     : result['timestamp']    if "timestamp"   in result else -1,
                        }
                    
                    data.append(machine_data)
            else:
                logging.error(f"Unknow record type: {record_type}")
              
            
            if to_topic is not '':
                self.publish(to_topic, json.dumps(data), qos=1)

        elif "/TLP/Thunghiem" in topic:
            logging.critical(f"Start trial production period {topic}")
            logging.critical("Doing NOTHING for now")
        else:
            logging.error(f"Unkown topic: {topic}")
        
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