from configure import *
import coloredlogs, os, redis
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_mqtt import Mqtt
import logging, time

# logging.basicConfig(filename='logging.log',level=logging.INFO)
"""
Configure log
"""
coloredlogs.install(level='error', fmt = '[%(hostname)s] [%(filename)s:%(lineno)s - %(funcName)s() ] %(asctime)s %(levelname)s %(message)s' )

"""
Configure Flask and database
"""
APP_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_PATH = os.path.join(APP_PATH, 'app')
print(TEMPLATE_PATH)

app = Flask(__name__, template_folder=TEMPLATE_PATH)

CORS(app)
SQL_URI = "sqlite:///"+ APP_PATH +"/"+ GeneralConfig.DATAFILE
app.config["SQLALCHEMY_DATABASE_URI"] = SQL_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
# app.config['SQLALCHEMY_POOL_SIZE'] = 20

db=SQLAlchemy(app=app)

"""
Config redis
"""
redisClient = redis.Redis(
        host= RedisCnf.HOST,
        port= RedisCnf.PORT, 
        password=  RedisCnf.PASSWORD,
        charset="utf-8",
        decode_responses = True
    )

app.config['MQTT_BROKER_URL'] = MQTTCnf.BROKER
app.config['MQTT_BROKER_PORT'] = MQTTCnf.PORT
app.config['MQTT_USERNAME'] = MQTTCnf.MQTT_USERNAME
app.config['MQTT_PASSWORD'] = MQTTCnf.MQTT_PASSWORD
app.config['MQTT_REFRESH_TIME'] = 1.0  # refresh time in seconds
app.config['MQTT_KEEPALIVE'] = 5  # set the time interval for sending a ping to the broker to 5 seconds
app.config['MQTT_TLS_ENABLED'] = False  # set TLS to disabled for testing purposes
app.config['MQTT_CLEAN_SESSION'] = True

mqtt = Mqtt(app)
time.sleep(1)
mqtt.subscribe(MQTTCnf.RATETOPIC)
mqtt.subscribe('/rostek/cmd')
from app.mqtt_handler import *

from app.action.service_utils import init_objects
init_objects()

