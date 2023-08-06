
import logging
from sqlalchemy import Column, Integer, String, Float, Boolean

from app import db_client
"""
Database for saving events
TO DO: update auto clean after ... days
"""

class MachineData(db_client.Model):
    __tablename__ = "Machine Data"

    id                  = Column("id", Integer, primary_key=True, autoincrement=True)
    deviceId            = Column("deviceId", String(16), nullable=False)
    machineStatus       = Column("machineStatus", Integer, nullable=False)
    errorCode           = Column("errorCode", Integer, nullable=False)
    output              = Column("output", Integer, nullable=False)
    input               = Column("input", Integer, nullable=False)
    runningNumber       = Column("runningNumber", Integer, nullable=False)
    envTemp             = Column("envTemp", Float)
    envHum              = Column("envHum", Float)
    waterTemp           = Column("waterTemp", Float)
    waterpH             = Column("waterpH", Float)
    timestamp           = Column("timestamp", Integer)
    uv1                 = Column("uv1", Integer)
    uv2                 = Column("uv2", Integer)
    uv3                 = Column("uv3", Integer)
    upperAirPressure    = Column("upperAirPressure", Integer)
    lowerAirPressure    = Column("lowerAirPressure", Integer)
    gluePressure        = Column("gluePressure", Float)
    glueTemp            = Column("glueTemp", Float)
    isChanging          = Column("isChanging", Boolean)


class UnsyncedMachineData(db_client.Model):
    """
    Cached database, when sending successful, clear record
    """
    __tablename__ = "Unsynced Machine Data"

    id              = Column("id", Integer, primary_key=True, autoincrement=True)
    deviceId        = Column("device_id", String(16), nullable=False)
    machineStatus   = Column("machine_status", Integer, nullable=False)
    actual          = Column("actual", Integer, nullable=False)
    runningNumber   = Column("runningNumber", Integer, nullable=False)
    timestamp       = Column("timestamp", Integer)
    temperature     = Column("temperature", Float)
    humidity        = Column("humidity", Float)
    isChanging      = Column("isChanging", Boolean)

