import pika
from utils.threadpool import ThreadPool
import time
import logging

class RabbitMQ():
    __instance = None
    @staticmethod
    def getInstance():
        if RabbitMQ.__instance == None:
            RabbitMQ()
        return RabbitMQ.__instance
    
    def __init__(self,id,password,broker,port, numthreads=5):
        if RabbitMQ.__instance != None:
            raise Exception("Do not call __init__(). RabbitMq is a singleton!")
        else:
            RabbitMQ.__instance = self
        self.__broker       = broker
        self.__port         = port
        # self.__connected    = False
        # self.__reconnecting = False
        self.__credentials  = pika.PlainCredentials(id, password)
        # self.__worker       = ThreadPool(numthreads)
        # self.__connection   = None
        # self.__worker.add_task(self.__check_rabbit_mq_connection)
        
        # V2
        self.connection     = None
        self.channel        = None
        self.establish_connection_sync()
        self.channel.queue_declare(queue="gateway_v3")
        self.channel.queue_declare(queue="oee_statistic")
    
    def establish_connection_sync(self, timesleep=1):
        while True:
            try:
                self.connection = pika.BlockingConnection(pika.ConnectionParameters(
                                    host=self.__broker,  
                                    port=self.__port,
                                    heartbeat=600,
                                    credentials=self.__credentials,
                                    blocked_connection_timeout=300)
                                    )
                self.channel    = self.connection.channel()

            except pika.exceptions.AMQPConnectionError:
                logging.error("Error: Unable to connect to RabbitMQ server. Retrying...")
                time.sleep(timesleep)  # Wait for 1 second before retrying
            except Exception as e:
                logging.error(f"Error: An unexpected error occurred: {e}")

    # def __connect(self):
    #     try:
    #         if not self.__connection or self.__connection.is_closed:
    #             logging.warning(f"Rabbit connected to broker: {self.__broker}")
    #             self.__connection  = pika.BlockingConnection(pika.ConnectionParameters(host=self.__broker,  port=self.__port,heartbeat=600,credentials=self.__credentials,blocked_connection_timeout=300))
    #             self.__channel = self.__connection.channel()
    #             self.__channel.queue_declare(queue="gateway_v3")
    #             self.__channel.queue_declare(queue="oee_statistic")
    #             self.__connected    = True
    #             self.__reconnecting = False
    #     except:
    #         logging.warning("Rabbit connection failed")
    #         self.__connected = False
    #         self.__reconnect()

    # def __reconnect(self, sleeptime=5):
    #     logging.warning("Trying to reconnect rabbit")
    #     time.sleep(sleeptime)
    #     self.__reconnecting = True
    #     self.__connect()
        

    # def __check_rabbit_mq_connection(self):
    #     """
    #     Check if rabbit connected, auto reconnect if disconnect
    #     """
    #     # pass
    #     while True:
    #         if not self.__connected and not self.__reconnecting:
    #             logging.warning("Rabbit not connected")
    #             self.__connect()
    #         time.sleep(1)
    
    # def get_channel(self):
    #     return self.__channel

    def disconnect(self):
        logging.info("Disconnecting to RabbitMQ server...")
        if self.connection and self.connection.is_open:
            self.connection.close()
            logging.debug('Closed connection!')
        else:
            logging.debug('Connection already disconnected!')
        
    # def connected(self):
    #     return self.__connected

    # def send_msg(self,data):
    #     if self.__connected:
    #         try:
    #             self.__channel.basic_publish(exchange='', routing_key='oee_data', body=data)
    #         except:
    #             self.set_disconnect()
    #             self.send_msg(data)
    
    def send_msgV2(self, data, routing_key='oee_data'):
        """
            - Return True/False
        """
        # self.connection = self.establish_connection_sync()
        # channel = self.connection.channel()

        if isinstance(routing_key, None):
            logging.error("Error! Invalid routing key=%s".format(routing_key))
            return False
        
        # channel.queue_declare(queue=queuename)

        try:
            self.channel.basic_publish(exchange='',
                                routing_key=routing_key,
                                body=data)
            return True
        except pika.exceptions.AMQPConnectionError:
            logging.error("Error: Connection lost. Reconnecting...")
            self.connection = self.establish_connection_sync()
            self.channel = self.connection.channel()
            self.send_msgV2(data, routing_key)
