from configure import *
import coloredlogs, os, redis
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import logging
# logging.basicConfig(filename='logging.log',level=logging.INFO)
"""
Configure log
"""
coloredlogs.install(level='warning', fmt = '[%(hostname)s] [%(filename)s:%(lineno)s - %(funcName)s() ] %(asctime)s %(levelname)s %(message)s' )

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
# redisClient.hset("/loop", "active", 0)
# logging.error("Okkkkkkkkk")
from app.action.service_utils import init_objects
init_objects()

