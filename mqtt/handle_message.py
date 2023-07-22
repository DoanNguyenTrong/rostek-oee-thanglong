from configure import deltaConfigure
import logging
import json
from app.service_utils import set_current_shift, reset_task

def handle_shift_data(deviceId,data,redisClient):
    """
    Handle with shift data
    """
    # logging.error(data)
    for device in deltaConfigure["LISTDEVICE"]:
        if deviceId == device["ID"]:
            # logging.warning(data)
            set_current_shift(deviceId,data,redisClient)
            reset_task(deviceId, data,redisClient)
                # schedule.every(5).seconds.do(start_shift, deviceId,redisClient,data[key],data[key]["start_time"])
    # schedule.run_pending()

def handle_production_data(deviceId,data,redisClient):
    """
    Handle production data
    """
    redisTopic = "/device/V2/" + deviceId + "/production"
    # logging.error(redisTopic)
    for key in data.keys():
        redisClient.hset(redisTopic, key, str(data[key]))
    # logging.error(data)