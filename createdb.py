
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import logging
from configure import GeneralConfig

DIR_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# SQL local database
SQL_URI = "sqlite:///"+ DIR_PATH +"/"+ GeneralConfig.DATAFILE


# Define the model
Base = declarative_base()

class MachineData(Base):
    __tablename__ = "Machine Data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    deviceId = Column(String(16), nullable=False)
    machineStatus = Column(Integer, nullable=False)
    errorCode = Column(Integer, nullable=False)
    output = Column(Integer, nullable=False)
    input = Column(Integer, nullable=False)
    runningNumber = Column(Integer, nullable=False)
    envTemp = Column(Float)
    envHum = Column(Float)
    waterTemp = Column(Float)
    waterpH = Column(Float)
    timestamp = Column(Integer)
    uv1 = Column(Integer)
    uv2 = Column(Integer)
    uv3 = Column(Integer)
    upperAirPressure = Column(Integer)
    lowerAirPressure = Column(Integer)
    gluePressure = Column(Float)
    glueTemp = Column(Float)
    isChanging = Column(Boolean)


# Create the database engine and tables
engine = create_engine(SQL_URI)
Base.metadata.create_all(engine)

# Create a session to interact with the database
Session = sessionmaker(bind=engine)
session = Session()
session.commit()

# Close the session when done
session.close()
print (SQL_URI)
