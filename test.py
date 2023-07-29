from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from configure import GeneralConfig
# from app.model.data_model import MachineData, Base
from app.model.unsynced_data import UnsyncedMachineData
from datetime import datetime
from sqlalchemy import and_
 
# engine = create_engine("sqlite:///"+ GeneralConfig.DATAFILE)
# Base.metadata.create_all(engine)
    
# # session = Session(engine)
# # results = session.query(MachineData).all()
# # for result in results:
# #     print(result.deviceId)
# #     print(result.timestamp)


# def query_by_date(timeFrom, timeTo, deviceId):
#     session = Session(engine)
#     results = session.query(MachineData).filter(and_(MachineData.timestamp >= timeFrom,MachineData.timestamp <= timeTo, MachineData.deviceId == deviceId)).all()
#     # results = session.query(MachineData).all()
#     for result in results:
#         print(result.deviceId)
#         print(result.timestamp)

# # query_by_date(datetime.fromtimestamp(1690266098),datetime.fromtimestamp(1690266098+10))
# query_by_date(1690266098,1690266098+10, "test9")

result = UnsyncedMachineData.query.order_by(UnsyncedMachineData.id.desc()).first()