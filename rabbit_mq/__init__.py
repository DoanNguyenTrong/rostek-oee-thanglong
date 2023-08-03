import time
import logging
import pika


class RabbitMQ():
    __instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance
    
    def __init__(self, id, password, broker, port):
        
        self.__broker       = broker
        self.__port         = port
        self.__credentials  = pika.PlainCredentials(id, password)
        self.__id           = id
        self.__password     = password
        
        # V2
        self.connection     = None
        self.channel        = None
        self.queues         = []
        
        
    def on_confirm(self, method_frame):
        if method_frame.method.NAME == 'Basic.Ack':
            logging.warning("Message published successfully.")
        else:
            logging.warning("Message not confirmed by the server.")
    
    def on_reject(self, method_frame):
        logging.error("Message rejected by the broker.")
        logging.error(f"Returned reply code: {method_frame.method.reply_code}")
        logging.error(f"Returned reply text: {method_frame.method.reply_text}")

    def setup(self, queues:list=['oee_data'], timesleep=5.0):
        while True:
            try:
                logging.debug("Trying to connect ...")
                self.connection = pika.BaseConnection(
                                        host=self.__broker,  
                                        port=self.__port,
                                        heartbeat=600,
                                        credentials=self.__credentials,
                                        blocked_connection_timeout=300)
                
                self.channel = self.connection.channel()
                
                # Enable message publisher confirms (acknowledgments)
                self.channel.confirm_delivery()

                self.channel.add_on_return_callback(self.on_reject)
                # self.channel.add_on_cancel_callback(self.on_confirm)
                # self.channel.basic_ack(self.on_confirm)
                
                for queue in queues:
                    if isinstance(queue, str):
                        self.queues.append( self.channel.queue_declare(queue=queue) )

                
            except pika.exceptions.AMQPError as e:
                print(f"Message publishing failed: {e}")
            except Exception as e:
                logging.error(f"Error: An unexpected error occurred: {e}")
                time.sleep(timesleep)  # Wait before retrying
            else:
                logging.debug("Connected successfully")
                break
    
    async def send_msgV2(self, data, routing_key='oee_data'):
        """
            - Return True/False
        """

        try:
            # Publish a message
            self.channel.basic_publish(exchange='',
                                       routing_key=routing_key,
                                       body=data,
                                       properties=pika.BasicProperties(content_type='text/plain',
                                                                       delivery_mode=pika.DeliveryMode.Persistent),
                                        mandatory=True
            )

            
        except Exception as e:
            logging.error(f"Error: An unexpected error occurred: {e}")


    def close(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            
