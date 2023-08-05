from rabbit_mq import RabbitMQ
import coloredlogs, os, redis
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import logging
import asyncio

# logging.basicConfig(filename='logging.log',level=logging.INFO)
"""
Configure log
"""
coloredlogs.install(level='info', fmt = '[%(hostname)s] [%(filename)s:%(lineno)s - %(funcName)s() ] %(asctime)s %(levelname)s %(message)s' )


"""
Configure Flask and database
"""
DIR_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_PATH = os.path.join(DIR_PATH, 'app')

logging.debug(DIR_PATH, APP_PATH)

app = Flask(__name__, template_folder=APP_PATH)

# Flask Cross Origin Resource Sharing
CORS(app)

# SQL local database
from configure import GeneralConfig
SQL_URI = "sqlite:///"+ DIR_PATH +"/"+ GeneralConfig.DATAFILE
app.config["SQLALCHEMY_DATABASE_URI"] = SQL_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db_client = SQLAlchemy(app=app)

from configure import RedisCnf
redis_client = redis.Redis(
        host= RedisCnf.HOST,
        port= RedisCnf.PORT, 
        password=  RedisCnf.PASSWORD,
        charset="utf-8",
        decode_responses = True
    )

from mqtt.mqtt_client import MQTTClient
from configure import MQTTCnf
mqtt_publisher = MQTTClient(MQTTCnf.BROKER_IP,
                         MQTTCnf.PORT,
                         client_name="DVES_E94F2C",
                         mqtt_data={"redisClient": redis_client}
                         )

from rabbit_mq.rabbit_client import RabbitMQPublisher
from configure import RabbitMQCnf
rabbit_publisher = RabbitMQPublisher(RabbitMQCnf.USER_ID,
                                     RabbitMQCnf.PASSWORD,
                                     RabbitMQCnf.BROKER,
                                     RabbitMQCnf.PORT
                                     )

# hardware device
from machine.delta_sa2 import DELTA_SA2_Modbus, RedisMonitor
from configure import deltaConfigure, RedisCnf
plc_modbus  = DELTA_SA2_Modbus(deltaConfigure)
redis_db_client = RedisMonitor(redis_client=redis_client,
                               sql_database_client=db_client,
                               configure=RedisCnf)

from app.main import main
asyncio.run(main(rabbit_publisher, mqtt_publisher, redis_db_client, db_client, plc_modbus))
