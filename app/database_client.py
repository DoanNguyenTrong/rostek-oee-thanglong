from configure import STATUS

import logging
import app.utils.vntime as VnTimeStamps
from app.mqtt_client import MQTTClient

import json

class RedisMonitor():
    def __init__(self, redis_client, sql_database_client, configure, MachineDataModel) -> None:
        self.configure = configure
        self.redis_client = redis_client
        self.sql_database_client = sql_database_client
        self.MachineData = MachineDataModel

    def get_redis_data(self, topic:str) -> dict:
        """
        Load old data from redis
        """
        logging.debug("Execute: get_redis_data()")
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
    
    def compare(self,
                mqtt_publisher:MQTTClient, 
                redis_data:dict, 
                current_data:dict):
        """
            Compare the difference between current and previous data 
        """
        logging.debug("Execute: compare()")
        logging.debug(f"Current: {current_data}")
        logging.debug(f"Redis  : {redis_data}")
        
        try:
            status_changed    = True if redis_data["status"] !=current_data["status"] else False
            output_changed    = True if redis_data["output"] != current_data["output"] else False
            input_changed     = True if redis_data["input"] != current_data["input"] else False
            error             = True if redis_data["errorCode"] != current_data["errorCode"] else False
            product_changed   = self._is_changing_product(redis_data, current_data["changeProduct"], mqtt_publisher)
            
            if status_changed or output_changed or input_changed or product_changed or error:
                return True
        except Exception as e:
            logging.error(e.__str__())
        return False
    
    def extract_dict_by_keys(self, 
                             input_data:dict, 
                             input_keys:list,
                             output_keys:list,
                             default=-1) -> dict:
        """
            Extract a subset of key-value pairs of a dictionary,
            assign to default values if not exist in original dict
        """
        logging.debug(f"Extracting by keys: {input_keys}")
        
        output_data = dict()
        if len(input_keys) == len(output_keys):
            for idx, key in enumerate(input_keys):
                if isinstance(key, str):
                    output_data[output_keys[idx]] = input_data[key] if key in input_data else default
        else:
            logging.error(f"Input and output keys are different in length: {len(input_keys)} vs {len(output_keys)}")
        return output_data
    
    def save_to_sql(self, device_id:str, current_data:dict):
        timeNow = int(VnTimeStamps.now())
        current_data["timestamp"]  = timeNow
        data = self.MachineData(
            deviceId            = device_id,
            machineStatus       = current_data['status'] if 'status' in current_data else None,
            output              = current_data['output'] if 'output' in current_data else None,
            input               = current_data['input'] if 'input' in current_data else None,
            errorCode           = current_data["errorCode"]if 'errorCode' in current_data else None,
            envTemp             = current_data["envTemp"]if 'envTemp' in current_data else None,
            envHum              = current_data["envHum"]if 'envHum' in current_data else None,
            waterTemp           = current_data["waterTemp"]if 'waterTemp' in current_data else None,
            waterpH             = current_data["waterpH"]if 'waterpH' in current_data else None,
            timestamp           = timeNow,
            uv1                 = current_data["uv1"]if 'uv1' in current_data else None,
            uv2                 = current_data["uv2"]if 'uv2' in current_data else None,
            uv3                 = current_data["uv3"]if 'uv3' in current_data else None,
            upperAirPressure    = current_data["upperAirPressure"]if 'upperAirPressure' in current_data else None,
            lowerAirPressure    = current_data["lowerAirPressure"]if 'lowerAirPressure' in current_data else None,
            gluePressure        = current_data["gluePressure"]if 'gluePressure' in current_data else None,
            glueTemp            = current_data["glueTemp"]if 'glueTemp' in current_data else None,
            isChanging          = current_data["isChanging"]if 'isChanging' in current_data else None,
            runningNumber       = current_data["runningNumber"]if 'runningNumber' in current_data else 0,
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
    
    def _is_changing_product(self, data:dict, changeProduct, mqtt_publisher:MQTTClient):
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
            mqtt_publisher.publish(mqtt_publisher.configures.STARTPRODUCTION, 
                                   json.dumps(self._generate_start_production_msg(data['deviceId'], now)))
            return True
        else:
            return False
    
    def _generate_start_production_msg(self, deviceId, now):
        return {
            "record_type"   : "tsl",
            "machine_id"    : deviceId,
            "timestamp"     : now
        }
    
    def _is_error(self, data:dict, errorCode):
        """
        Check if error
        """
        if data["errorCode"] != errorCode:
            logging.error(f"Error code change, previous errorCode: {data['errorCode']} - current Error code {errorCode}")
            # data["errorCode"] = errorCode
            return True
        return False
