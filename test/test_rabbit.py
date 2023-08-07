import aio_pika
import asyncio
import logging
from pamqp.commands import Basic
from configure import *
import time
from datetime import datetime

class RabbitMQPublisher:
    def __init__(self, id, password, broker, port):
        self.__broker       = broker
        self.__port         = port
        self.__id           = id
        self.__password     = password
        
        self.connection     = None
        self.channel        = None
        self.queues         = []

    async def on_confirm(self, message):
        if message:
            success_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"Message published successfully at {success_time}.")
        else:
            print("Message not confirmed by the server.")

    async def on_return(self, message):
        print(f"Message returned by RabbitMQ: {message}")

        
    async def setup(self):
        self.connection = await aio_pika.connect_robust(host=self.__broker, 
                                                        port=self.__port, 
                                                        # timeout=600, 
                                                        login=self.__id, 
                                                        password=self.__password)
        self.channel = await self.connection.channel(publisher_confirms=True)

        # # Enable message publisher confirms (acknowledgments)
        # await self.channel.confirm_select()

        # Set the on_confirm callback to be invoked when a message is confirmed
        # self.channel.default_exchange.on_return_raises = False
        # self.channel.default_exchange.on_return(self.on_confirm)

        # Replace 'your_queue_name' with the appropriate queue name.
        self.queues = await self.channel.declare_queue("test_data")

    async def send_message(self, data):
        # Publish a message
        try:
            logging.info(f'Start sending at {time.time()}')

            message = aio_pika.Message(body=data.encode())
            # Wait for the message to be confirmed
            confirm = await self.channel.default_exchange.publish(
                message,
                routing_key='test_data',
                mandatory=True,  # Enable message return callback
            )

            # await confirm

        except aio_pika.exceptions.DeliveryError as e:
            logging.error(f"Delivery of {message!r} failed with exception: {e}")
        except TimeoutError:
            logging.error(f"Timeout occured for {message!r}")
        except Exception as e:
            logging.error(f'Unknown exception: {e}')
        else:
            if not isinstance(confirm, Basic.Ack):
                logging.debug(f"Message {message!r} was not acknowledged by broker!")
            else:
                success_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logging.warning(f"{success_time} Message published successfully.{confirm}")
    
    async def close(self):
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
    

async def main():
    publisher = RabbitMQPublisher(RabbitMQCnf.USER_ID,RabbitMQCnf.PASSWORD,RabbitMQCnf.BROKER, RabbitMQCnf.PORT)
    await publisher.setup()

    try:
        data = "{'deviceId': 'DVES_E94F2H', 'machineStatus': 1, 'actual': 26, 'runningNumber': 3, 'timestamp': 1691043738, 'isChanging': False}"

        while True:
            input_str = await asyncio.to_thread(input, "Type 'pub' and press Enter to send a message: ")
            if input_str.strip() == "pub":
                await publisher.send_message(data)
            else:
                print("Invalid input. Please try again.")

    except KeyboardInterrupt:
        print("KeyboardInterrupt received. Closing the publisher...")

    except aio_pika.exceptions.AMQPError as e:
        print(f"Message publishing failed: {e}")
    finally:
        await publisher.close()

# Run the main coroutine
if __name__ == "__main__":
    asyncio.run(main())