import logging
from datetime import datetime

import coloredlogs, os, redis
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import asyncio

import app.mqtt_client as mqtt_client
import configure 
import app.rabbit_client as rabbit_client

# logging.basicConfig(filename='logging.log',level=logging.INFO)
"""
Configure log
"""
# Determine the absolute path for the log directory
log_directory = os.path.abspath("logs")

# Create a sub-folder based on the current time down to minutes
current_time = datetime.now().strftime("%Y-%m-%d_%H-%M")
log_subfolder = f"{log_directory}/{current_time}"
os.makedirs(log_subfolder, exist_ok=True)

# Get the name of the current module's .py file
module_name = os.path.splitext(os.path.basename(__file__))[0]

# Configure logging to a file
log_format = (
    "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - "
    "%(funcName)s() - %(message)s"
)

log_filename = f"{log_subfolder}/{__name__}.log"
log_level = logging.DEBUG
logging.basicConfig(
    format=log_format, level=log_level, filename=log_filename, filemode="a"
)
fmt = '[%(hostname)s] [%(filename)s:%(lineno)s - %(funcName)s() ] %(asctime)s %(levelname)s %(message)s'
coloredlogs.install(level='debug',fmt=fmt)


"""
Configure Flask and database
"""
DIR_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_PATH = os.path.join(DIR_PATH, 'app')

logging.debug(f"{DIR_PATH},{APP_PATH}")

app = Flask(__name__, template_folder=APP_PATH)

# Flask Cross Origin Resource Sharing
CORS(app)

# SQL local database
SQL_URI = "sqlite:///"+ DIR_PATH +"/"+ configure.GeneralConfig.DATAFILE
app.config["SQLALCHEMY_DATABASE_URI"] = SQL_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db_client = SQLAlchemy(app=app)


redis_obj = redis.Redis(
        host = configure.RedisCnf.HOST,
        port = configure.RedisCnf.PORT, 
        password =  configure.RedisCnf.PASSWORD,
        charset ="utf-8",
        decode_responses = True
    )

mqtt_publisher = mqtt_client.MQTTClient(configures=configure.MQTTCnf,
                        user_data={"redisClient": redis_obj}
                        )


rabbit_publisher = rabbit_client.RabbitMQPublisher(configure.RabbitMQCnf.USER_ID,
                                    configure.RabbitMQCnf.PASSWORD,
                                    configure.RabbitMQCnf.BROKER,
                                    configure.RabbitMQCnf.PORT
                                    )



from app.action.services import rostek_oee
asyncio.run(rostek_oee(rabbit_publisher, mqtt_publisher, redis_obj))