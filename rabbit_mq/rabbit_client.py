import time
import logging
import aio_pika
import asyncio
from pamqp.commands import Basic
from datetime import datetime


class RabbitMQPublisher():
    __instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance
    
    async def on_confirm(self, message):
        if message:
            success_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logging.debug(f"Message published successfully at {success_time}.")
        else:
            logging.debug("Message not confirmed by the server.")

    async def on_return(self, message):
        logging.debug(f"Message returned by RabbitMQ: {message}")

    def __init__(self, id, password, broker, port):
        self.__broker       = broker
        self.__port         = port
        self.__id           = id
        self.__password     = password
        
        self.connection     = None
        self.channel        = None
        self.queues         = []
    
    async def setup(self, routing_key:list=['oee_data']):
        logging.info("Setup RabbitMQ Publisher ....")
        
        self.connection = await aio_pika.connect_robust(host=self.__broker, 
                                                        port=self.__port, 
                                                        # timeout=600, 
                                                        login=self.__id, 
                                                        password=self.__password)
        self.channel    = await self.connection.channel(publisher_confirms=True)

        # # Enable message publisher confirms (acknowledgments)
        # await self.channel.confirm_select()

        # Set the on_confirm callback to be invoked when a message is confirmed
        # self.channel.default_exchange.on_return_raises = False
        # self.channel.default_exchange.on_return(self.on_confirm)

        for queue_name in routing_key:
            if isinstance(queue_name, str):
                self.queues.append( await self.channel.declare_queue(queue_name) )
                logging.debug(f"Constructed a new queue: {queue_name}")
            else:
                raise Exception(f"Queue name is not a str, {queue_name}")
    
    async def send_message(self, data:tuple, 
                           queue_name="oee_data", 
                           timeout:float=5.0):
        try:
            send_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Publish a message
            logging.warning(f'{send_time} Trigger sending data to {queue_name}')
            message = aio_pika.Message(body=data.encode('utf-8'),
                                   content_type='text/plain',
                                   delivery_mode=aio_pika.DeliveryMode.PERSISTENT)
            
            confirmation = await self.channel.default_exchange.publish(message, 
                                                        routing_key=queue_name, 
                                                        timeout=timeout,
                                                        mandatory=True)

        except aio_pika.exceptions.DeliveryError as e:
            logging.error(f"Delivery of {message!r} failed with exception: {e}")
        except TimeoutError:
            logging.error(f"Timeout occured for {message!r}")
        except Exception as e:
            logging.error(f'Unknown exception: {e}')
        else:
            if not isinstance(confirmation, Basic.Ack):
                logging.debug(f"Message {message!r} was not acknowledged by broker!")
            else:
                success_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logging.warning(f"{success_time} Message published successfully.{confirm}")
        
    async def close(self):
        try:
            await self.connection.close()
        except aio_pika.exceptions.AMQPException as e:
            logging.error(f"Error while closing the connection: {e}")
