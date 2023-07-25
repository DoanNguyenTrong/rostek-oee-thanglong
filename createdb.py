from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from configure import GeneralConfig
from app.model.data_model import MachineData, Base
from datetime import datetime
 
 
timestamp = 1690266098
dt_obj = datetime.fromtimestamp(timestamp)

engine = create_engine("sqlite:///"+ GeneralConfig.DATAFILE)
Base.metadata.create_all(engine)

for i in range(10):
    value = MachineData(
    deviceId            = "test"+str(i), 
    machineStatus       = 1,
    actual              = 10,
    # timestamp           = datetime.fromtimestamp(timestamp+i),
    timestamp           = timestamp+i,
    humidity            = 10,
    runningNumber       = 11,
    temperature         = 30
    )
    session = Session(engine)
    session.add(value)
    session.commit()
    print("Init Database Done !")