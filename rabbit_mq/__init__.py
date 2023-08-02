import pika
from utils.threadpool import ThreadPool
import time
import logging
import pika

class RabbitMQ():
    __instance = None
    @staticmethod
    def getInstance():
        if RabbitMQ.__instance == None:
            RabbitMQ()
        return RabbitMQ.__instance
    
    def __init__(self,id,password,broker,port):
        if RabbitMQ.__instance != None:
            raise Exception("Do not call __init__(). RabbitMq is a singleton!")
        else:
            RabbitMQ.__instance = self
        self.__broker       = broker
        self.__port         = port
        self.__connected    = False
        self.__reconnecting = False
        self.__credentials  = pika.PlainCredentials(id, password)
        self.__worker       = ThreadPool(5)
        self.__connection   = None
        self.__worker.add_task(self.__check_rabbit_mq_connection)
        
    def __connect(self):
        try:
            if not self.__connection or self.__connection.is_closed:
                logging.warning(f"Rabbit connected to broker: {self.__broker}")
                self.__connection  = pika.BlockingConnection(pika.ConnectionParameters(host=self.__broker,  port=self.__port,heartbeat=600,credentials=self.__credentials,blocked_connection_timeout=300))
                self.__channel = self.__connection.channel()
                self.__channel.queue_declare(queue="gateway_v3")
                self.__channel.queue_declare(queue="oee_data")
                self.__connected    = True
                self.__reconnecting = False
        except:
            logging.warning("Rabbit connection failed")
            self.__connected = False
            self.__reconnect()

    def __reconnect(self):
        logging.warning("Trying to reconnect rabbit")
        time.sleep(5)
        self.__reconnecting = True
        self.__connect()
        

    def __check_rabbit_mq_connection(self):
        """
        Check if rabbit connected, auto reconnect if disconnect
        """
        # pass
        while True:
            if not self.__connected and not self.__reconnecting:
                logging.warning("Rabbit not connected")
                self.__connect()
            time.sleep(1)
    
    def get_channel(self):
        return self.__channel

    def set_disconnect(self):
        logging.error("Rabbit disconnected")
        self.__connected = False
        if self.__connection and self.__connection.is_open:
            logging.debug('closing queue connection')
            self.__connection.close()
        
    def connected(self):
        return self.__connected

    def send_msg(self,data):
        if self.__connected:
            try:
                self.__channel.basic_publish(exchange='', routing_key='oee_data', body=data)
            except:
                self.set_disconnect()
                self.send_msg(data)