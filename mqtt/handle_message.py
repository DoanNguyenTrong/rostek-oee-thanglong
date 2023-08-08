from configure import listConfig, RedisCnf
import logging
import json
import schedule
from app.action.service_utils import sync_quality_data, query_data, sync_machine_data, sync_production_data

def handle_rate_data(client,data,redisClient):
    """
    Handle refresh data rate
    """
    schedule.clear()
    recordType = data["record_type"]
    if recordType == "sx":
        redisClient.hset(RedisCnf.RATETOPIC, "production", data["frequency"])
        schedule.every(data["frequency"]).seconds.do(sync_production_data)

    elif recordType == "cl":
        redisClient.hset(RedisCnf.RATETOPIC, "quality", data["frequency"])
        schedule.every(data["frequency"]).seconds.do(sync_quality_data)

    elif recordType == "tb":
        redisClient.hset(RedisCnf.RATETOPIC, "machine", data["frequency"])
        schedule.every(data["frequency"]).seconds.do(sync_machine_data)

    logging.error(f"Scheduled every {data['frequency']} secs for {recordType} !")

def handle_request_data(deviceId,data,client):
    """
    Handle data request from server
    """
    timeFrom    = data["from"]
    timeTo      = data["to"]
    data = query_data(str(deviceId, timeFrom, timeTo))
    client.publish(json.dumps(data))

