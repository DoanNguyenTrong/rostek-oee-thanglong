from configure import GeneralConfig
from app.model.data_model import *
from app.model.unsynced_data import *
from sqlalchemy_utils import create_database, database_exists
from app import db, SQL_URI
print(SQL_URI)
if not database_exists(SQL_URI):
    create_database(SQL_URI)
db.drop_all()
db.create_all()

print("Init Database Done !")
