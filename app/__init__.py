from configure import RedisCnf
from configure import *
import coloredlogs, os, redis
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

# logging.basicConfig(filename='logging.log',level=logging.INFO)
coloredlogs.install(level='info', fmt = '[%(hostname)s] [%(filename)s:%(lineno)s - %(funcName)s() ] %(asctime)s %(levelname)s %(message)s' )

APP_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_PATH = os.path.join(APP_PATH, 'app')
print(TEMPLATE_PATH)

app = Flask(__name__, template_folder=TEMPLATE_PATH)
CORS(app)
SQL_URI = "sqlite:///"+ GeneralConfig.DATAFILE
app.config["SQLALCHEMY_DATABASE_URI"] = SQL_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_POOL_SIZE'] = 20

##--CONFIGURE REDIS
db=SQLAlchemy(app=app)

redisClient = redis.Redis(
        host= RedisCnf.HOST,
        port= RedisCnf.PORT, 
        password=  RedisCnf.PASSWORD,
        charset="utf-8",
        decode_responses = True
    )
from app.action.service_utils import init_objects

init_objects()

