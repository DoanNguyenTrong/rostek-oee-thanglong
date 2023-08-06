from configure import STATUS

import logging
import app.utils.vntime as VnTimeStamps

from app.model.data_model import MachineData, UnsyncedMachineData

class RedisMonitor():
    def __init__(self, redis_client, sql_database_client, configure) -> None:
        self.configure = configure
        self.redis_client = redis_client
        self.sql_database_client = sql_database_client

    def get_redis_data(self, topic:str):
        """
        Load old data from redis
        """
        logging.debug("Execute: get_redis_data()")
        # rawTopic    = device["ID"] + "/raw"
        # TODO: why read all, can be the latest only?
        try:
            logging.debug(f"Query Redis topic:{topic}")
            redis_data  = self.redis_client.hgetall(topic)
            # logging.debug(f"Redis data:{redis_data}")

            redis_data["timestamp"]  = int(float(VnTimeStamps.now()))
            
            if "input" not in redis_data:
                redis_data["status"]         = STATUS.DISCONNECT
                redis_data["output"]         = 0
                redis_data["input"]          = 0
                redis_data["changeProduct"]  = 0
                redis_data["errorCode"]      = 0
            else: 
                redis_data["status"]         = int(redis_data["status"]) 
                redis_data["output"]         = int(redis_data["output"]) 
                redis_data["input"]          = int(redis_data["input"])
                redis_data["changeProduct"]  = int(redis_data["changeProduct"])
                redis_data["errorCode"]      = int(redis_data["errorCode"])
        except Exception as e:
            logging.error(e.__str__())
        logging.debug(f"Latest data: {redis_data}")
        return redis_data
    
    def compare(self, device_id, redis_data:dict, current_data:dict):
        logging.debug("Execute: compare()")
        logging.debug(f"Current: {current_data}")
        logging.debug(f"Redis  : {redis_data}")
        try:
            status_changed    = self._is_status_change      (redis_data, current_data["status"])
            output_changed    = self._is_output_change      (redis_data, current_data["output"])
            input_changed     = self._is_input_change       (redis_data, current_data["input"])
            product_changed   = self._is_changing_product   (redis_data, current_data["changeProduct"])
            error             = self._is_error              (redis_data, current_data["errorCode"])
            
            if status_changed or output_changed or input_changed or product_changed or error:
                return True
        except Exception as e:
            logging.error(e.__str__())
        return False
    
    def save_to_sql(self, device_id:str, current_data:dict):
        timeNow = int(float(VnTimeStamps.now()))
        current_data["timestamp"]  = timeNow
        data = MachineData(
            deviceId            = device_id,
            machineStatus       = current_data['status'],
            output              = current_data['output'],
            input               = current_data['input'],
            errorCode           = current_data["errorCode"],
            envTemp             = -1,
            envHum              = -1,
            waterTemp           = -1,
            waterpH             = -1,
            timestamp           = current_data["timestamp"],
            uv1                 = current_data["uv1"],
            uv2                 = current_data["uv2"],
            uv3                 = current_data["uv3"],
            upperAirPressure    = -1,
            lowerAirPressure    = -1,
            gluePressure        = -1,
            glueTemp            = -1,
            isChanging          = current_data["changeProduct"]
            )
        
        self._to_sql(data, data)
    
    def _to_sql(self, data, unsynced_data):    
        try:
            self.sql_database_client.session.add(data)
            self.sql_database_client.session.add(unsynced_data)
            self.sql_database_client.session.commit()
            self.sql_database_client.session.close() 
        except Exception as e:
            self.sql_database_client.session.rollback()
            self.sql_database_client.session.close() 
            logging.error(e.__str__())
        logging.debug("Complete saving data!")

    def save_to_redis(self, topic:str, data:dict):
        """
        Save raw data to redis
        """
        logging.debug(f"{topic}: {data}")
        for key in data.keys():
            self.redis_client.hset(topic,key ,data[key])

    def _is_status_change(self, data:dict, status):
        """
        Check if machine status change
        """
        if data["status"] != status:
            logging.debug(f"Status change, prev: {data['status']} - cur: {status}")
            # data["status"] = status
            return True
        return False
        
    def _is_actual_change(self, data:dict, actual):
        """
        Check if actual change
        """
        if data["actual"] != actual:
            logging.debug(f"Status change, prev: {data['actual']} - cur: {actual}")
            # data["actual"] = actual
            return True
        return False
    
    def _is_output_change(self, data:dict, output):
        """
        Check if actual change
        """
        if data["output"] != output:
            logging.debug(f"Status change, prev: {data['output']} - cur: {output}")
            # data["actual"] = actual
            return True
        return False
    
    def _is_input_change(self, data:dict, input_data):
        """
        Check if actual change
        """
        if data["input"] != input_data:
            logging.debug(f"Status change, prev: {data['input']} - cur: {input_data}")
            # data["actual"] = actual
            return True
        return False
    
    def _is_changing_product(self, data:dict, changeProduct):
        """
        Check if changing product
        """

        # TODO: need to be concatenated!
        now = VnTimeStamps.now()
        if data["changeProduct"] == 0 and changeProduct == 1:
            logging.debug(f"Start changing product, prev: {data['changeProduct']}, curr: {changeProduct}")
            return True
        elif data["changeProduct"] == 1 and changeProduct == 0:
            logging.debug(f"Stop changing product, cur: {data['changeProduct']}, curr: {changeProduct}")
            return True
        else:
            return False
    
    def _is_error(self, data:dict, errorCode):
        """
        Check if error
        """
        if data["errorCode"] != errorCode:
            logging.error(f"Error code change, previous errorCode: {data['errorCode']} - current Error code {errorCode}")
            # data["errorCode"] = errorCode
            return True
        return False
