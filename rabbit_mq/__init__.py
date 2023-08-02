import time
import logging
import aio_pika
import asyncio
from pamqp.commands import Basic

class RabbitMQ():
    __instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance
    
    # async def on_confirm(self, method_frame):
    #     if method_frame.method.NAME == 'Basic.Ack':
    #         logging.warning("Message published successfully.")
    #     elif method_frame.method.NAME == 'Basic.Nack':
    #         logging.warning("Message published but not confirmed by the server.")
    #     elif method_frame.method.NAME == 'Basic.Return':
    #         logging.warning("Message published but was returned by the server.")

    def __init__(self, id, password, broker, port):
        if RabbitMQ.__instance != None:
            raise Exception("Do not call __init__(). RabbitMq is a singleton!")
        else:
            RabbitMQ.__instance = self
        
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
                                                        timeout=600, 
                                                        login=self.__id, 
                                                        password=self.__password)
        self.channel    = await self.connection.channel(publisher_confirms=True)

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
            # Publish a message
            message = aio_pika.Message(body=data.encode(),
                                   content_type='text/plain',
                                   delivery_mode=aio_pika.DeliveryMode.PERSISTENT)
            
            confirmation = await self.channel.default_exchange.publish(message, 
                                                        routing_key=queue_name, 
                                                        timeout=timeout)

        except aio_pika.exceptions.DeliveryError as e:
            logging.error(f"Delivery of {message!r} failed with exception: {e}")
        except TimeoutError:
            logging.error(f"Timeout occured for {message!r}")
            self.setup()
            self.send_message(message)
        except Exception as e:
            logging.error(f'Unknown exception: {e}')
        else:
            if not isinstance(confirmation, Basic.Ack):
                logging.debug(f"Message {message!r} was not acknowledged by broker!")
        
    async def close(self):
        try:
            await self.connection.close()
        except aio_pika.exceptions.AMQPException as e:
            logging.error(f"Error while closing the connection: {e}")
