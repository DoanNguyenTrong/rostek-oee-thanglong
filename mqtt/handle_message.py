from configure import deltaConfigure
import logging
import json
import schedule
from app.service_utils import sync_humidity_temperature
from mqtt import mqtt_client

def handle_humtemp_rate_data(deviceId,data,redisClient):
    """
    Handle with humtemp data
    """
    schedule.clear()
    humTempRate = data["rate"]
    schedule.every(humTempRate).seconds.do(sync_humidity_temperature, deltaConfigure, redisClient, mqtt_client)