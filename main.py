import logging
from configure import  *
from app.model.plc_delta import DELTA_SA2
import time
from mqtt import mqtt_client
from app import *

def init_objects():
    logging.warning("Starting program")
    plcDelta = DELTA_SA2(redisClient,deltaConfigure)
    start_service(plcDelta,deltaConfigure,redisClient,mqtt_client)

if __name__ == "__main__":
    init_objects()
    while True:
        time.sleep(1)
