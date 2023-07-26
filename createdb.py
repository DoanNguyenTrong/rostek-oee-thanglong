from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from configure import GeneralConfig
from app.model.data_model import *
from app.model.unsynced_data import *
from datetime import datetime

engine = create_engine("sqlite:///"+ GeneralConfig.DATAFILE)
Base.metadata.create_all(engine)

print("Init Database Done !")
