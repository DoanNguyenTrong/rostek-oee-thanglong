import redis
from configure import RedisCnf
from utils.threadpool import ThreadPool
from app.service_utils import *
import coloredlogs
import schedule
from sqlalchemy import create_engine
import logging

# logging.basicConfig(filename='logging.log',level=logging.INFO)
coloredlogs.install(level='info', fmt = '[%(hostname)s] [%(filename)s:%(lineno)s - %(funcName)s() ] %(asctime)s %(levelname)s %(message)s' )
workers = ThreadPool(100)


engine = create_engine("sqlite:///"+ GeneralConfig.DATAFILE)

redisClient = redis.Redis(
        host= RedisCnf.HOST,
        port= RedisCnf.PORT, 
        password=  RedisCnf.PASSWORD,
        charset="utf-8",
        decode_responses = True
    )

def start_service(object,configure,redisClient,mqttClient):
    humTempRate = redisClient.hgetall(RedisCnf.HUMTEMPTOPIC)
    if "humtemprate" not in humTempRate:
        humTempRate = GeneralConfig.DEFAULTRATE 
    else:
        humTempRate = int(humTempRate)
    workers.add_task(object.start)
    workers.add_task(synchronize_data, configure, redisClient, mqttClient, engine)
    # schedule.every(humTempRate).seconds.do(sync_humidity_temperature, configure, redisClient, mqttClient)


def start_scheduling_thread():
    while True:
        schedule.run_pending()
        time.sleep(1)

workers.add_task(start_scheduling_thread)
