from configure import deltaConfigure
import logging
import json
import schedule
from app.service_utils import sync_humidity_temperature
from sqlalchemy import select
from app.service_utils import query_data

def handle_humtemp_rate_data(client,data,redisClient):
    """
    Handle humidity and temperature refresh data rate
    """
    schedule.clear()
    humTempRate = data["rate"]
    schedule.every(humTempRate).seconds.do(sync_humidity_temperature, deltaConfigure, redisClient, client)

def handle_request_data(deviceId,data,client):
    """
    Handle data request from server
    """
    timeFrom    = data["from"]
    timeTo      = data["to"]
    data = query_data(str(deviceId, timeFrom, timeTo))
    client.publish(json.dumps(data))