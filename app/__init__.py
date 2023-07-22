import redis
from configure import RedisCnf
from utils.threadpool import ThreadPool
from app.service_utils import *
import coloredlogs

logging.basicConfig(filename='logging.log',level=logging.INFO)
coloredlogs.install(level='info', fmt = '[%(hostname)s] [%(filename)s:%(lineno)s - %(funcName)s() ] %(asctime)s %(levelname)s %(message)s' )
workers = ThreadPool(100)

redisClient = redis.Redis(
        host= RedisCnf.HOST,
        port= RedisCnf.PORT, 
        password=  RedisCnf.PASSWORD,
        charset="utf-8",
        decode_responses = True
    )

def start_service(object,configure,redisClient,mqttClient):
    workers.add_task(object.start)
    workers.add_task(synchronize_data,configure,redisClient,mqttClient)
