import paho.mqtt.client as mqtt
import asyncio

class MqttHandler:
    def __init__(self, broker_address, broker_port, username, password):
        self.client = mqtt.Client()
        self.client.username_pw_set(username, password)
        self.client.on_publish = self.on_publish
        self.client.on_message = self.on_message
        self.client.on_subscribe = self.on_subscribe  # Add this line
        self.broker_address = broker_address
        self.broker_port = broker_port
        self.userdata = {'topic': None}

    def on_publish(self, client, userdata, mid):
        
        print("Message published with MID:", mid)
        print("Published Topic:", )

    def on_message(self, client, userdata, message):
        print("Received message on topic:", message.topic)
        print("Message payload:", message.payload.decode())

    def on_subscribe(self, client, userdata, mid, granted_qos):
        print("Subscribed to topic with MID:", mid)
        print("Granted QoS levels:", granted_qos)

    def connect(self):
        self.client.connect(self.broker_address, self.broker_port)
        self.client.loop_start()

    def subscribe(self, topic):
        self.client.subscribe(topic)

    def publish(self, topic, message):
        self.userdata['topic'] = topic
        # self.client.
        result, mid = self.client.publish(topic, message)
        return result, mid

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()

async def publish_task(mqtt_handler, publish_topic, message, publish_interval):
    while True:
        mqtt_handler.publish(publish_topic, message)
        await asyncio.sleep(publish_interval)

async def another_task():
    while True:
        print("Another task is running...")
        await asyncio.sleep(10)

async def main():
    from configure import MQTTCnf
    # MQTT broker details
    broker_address = MQTTCnf.BROKER_IP
    broker_port = MQTTCnf.PORT
    username = MQTTCnf.MQTT_USERNAME
    password = MQTTCnf.MQTT_PASSWORD

    # Create an instance of the MqttHandler class
    mqtt_handler = MqttHandler(broker_address, broker_port, username, password)

    # Connect to the broker
    mqtt_handler.connect()

    # Subscribe to the topic
    subscribe_topic = "/TLP/Fre"
    mqtt_handler.subscribe(subscribe_topic)

    # Start a task to handle publishing
    publish_topic = "/Rostek/test_subsribe"
    message = "Hello, MQTT!"
    publish_interval = 5
    publish_coroutine = publish_task(mqtt_handler, publish_topic, message, publish_interval)

    # Start the another_task
    another_coroutine = another_task()

    # Main loop to handle incoming messages and run tasks concurrently
    while True:
        await asyncio.gather(publish_coroutine, another_coroutine, asyncio.sleep(0))

    # Disconnect from the broker
    mqtt_handler.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
