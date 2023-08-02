import time
import logging
import aio_pika
import asyncio
from aio_pika import ExchangeType, connect
from aio_pika.abc import AbstractIncomingMessage

async def on_confirm(confirmation_frame):
    if confirmation_frame.method.NAME == 'Basic.Ack':
        logging.warning("Message published successfully.")
    elif confirmation_frame.method.NAME == 'Basic.Nack':
        logging.warning("Message published but not confirmed by the server.")
    elif confirmation_frame.method.NAME == 'Basic.Return':
        logging.warning("Message published but was returned by the server.")

async def on_message(message: AbstractIncomingMessage) -> None:
    async with message.process():
        logging.info(f"[x] {message.body!r}")


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
        # self.__credentials  = pika.PlainCredentials(id, password)
        self.__id = id
        self.__password = password
        
        # V2
        self.connection     = None
        self.channel        = None
        self.queue          = None

        self.establish_connection_sync()
        
        # self.channel.confirm_delivery()
        # self.channel.add_on_return_callback(on_confirm)
        
        # self.channel.queue_declare(queue="gateway_v3")
        # self.channel.queue_declare(queue="oee_data")
    
    async def establish_connection_sync(self, timesleep=1):
        while True:
            try:
                logging.debug("Trying to connect ...")
                self.connection = await connect(host=self.__broker, port=self.__port, timeout=600, login=self.__id, password=self.__password)
                # pika.ConnectionParameters(
                #                 host=self.__broker,  
                #                 port=self.__port,
                #                 heartbeat=600,
                #                 credentials=self.__credentials,
                #                 blocked_connection_timeout=300)
                #                 )
                async with self.connection:
                    # Creating a channel
                    self.channel = await self.connection.channel()
                    await self.channel.set_qos(prefetch_count=1)

                    logs_exchange = await self.channel.declare_exchange(
                        "logs", ExchangeType.FANOUT,
                    )

                    # Declaring queue
                    self.queue = await self.channel.declare_queue(name="oee_data",exclusive=True)

                    # Binding the queue to the exchange
                    await self.queue.bind(logs_exchange)

                    # Start listening the queue
                    await self.queue.consume(on_message)

                    print(" [*] Waiting for logs. To exit press CTRL+C")
                    await asyncio.Future()
                break
            except Exception as e:
                logging.error(f"Error: An unexpected error occurred: {e}")
                time.sleep(timesleep)  # Wait for 1 second before retrying
    
    async def send_msgV2(self, data, routing_key='oee_data'):
        """
            - Return True/False
        """

        try:

            # Publish a message
            await self.channel.default_exchange.publish(
                aio_pika.Message(body=data,
                                content_type='text/plain',
                                delivery_mode=aio_pika.DeliveryMode.PERSISTENT),
                routing_key=routing_key,
            )

            # Wait for confirms
            await self.channel._connection._flush_output()
            await on_confirm(await self.channel._connection._read_frame())
        except Exception as e:
            logging.error(f"Error: An unexpected error occurred: {e}")
            
