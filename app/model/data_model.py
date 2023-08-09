from sqlalchemy import Column, Integer, String, Float, Boolean
from app import db
"""
Database for saving events
TO DO: update auto clean after ... days
"""
class MachineData(db.Model):
    __tablename__ = "Machine Data"

    id                  = Column("id", Integer, primary_key=True, autoincrement=True)
    deviceId            = Column("deviceId", String(16), nullable=False)
    machineStatus       = Column("machineStatus", Integer, nullable=False)
    errorCode           = Column("errorCode", Integer, nullable=False)
    output              = Column("output", Integer, nullable=False)
    input               = Column("input", Integer, nullable=False)
    envTemp             = Column("envTemp", Float)
    envHum              = Column("envHum", Float)
    waterTemp           = Column("waterTemp", Float)
    waterpH             = Column("waterpH", String(1000))
    timestamp           = Column("timestamp", Integer)
    uv1                 = Column("uv1", Integer)
    uv2                 = Column("uv2", Integer)
    uv3                 = Column("uv3", Integer)
    upperAirPressure    = Column("upperAirPressure", Integer)
    lowerAirPressure    = Column("lowerAirPressure", Integer)
    gluePressure        = Column("gluePressure", Float)
    glueTemp            = Column("glueTemp", Float)
db.create_all()