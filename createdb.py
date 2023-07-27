from configure import GeneralConfig
# from app.model.data_model import *
# from app.model.unsynced_data import *
from app import db

db.drop_all()
db.create_all()

print("Init Database Done !")
