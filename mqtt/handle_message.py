from configure import deltaConfigure, RedisCnf
import logging
import json
import schedule
from app.main import sync_humidity_temperature, query_data

def handle_humtemp_rate_data(client,data,redisClient):
    """
    Handle humidity and temperature refresh data rate
    """
    schedule.clear()
    humTempRate = data["rate"]
    redisClient.hset(RedisCnf.HUMTEMPTOPIC, "humtemprate", humTempRate)
    schedule.every(humTempRate).seconds.do(sync_humidity_temperature, deltaConfigure, redisClient, client)
    logging.error(f"Scheduled every {humTempRate} secs !")

def handle_request_data(deviceId,data,client):
    """
    Handle data request from server
    """
    timeFrom    = data["from"]
    timeTo      = data["to"]
    data = query_data(str(deviceId, timeFrom, timeTo))
    client.publish(json.dumps(data))