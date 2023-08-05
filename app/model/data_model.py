
import logging
from sqlalchemy import Column, Integer, String, Float, Boolean

from app import db_client
"""
Database for saving events
TO DO: update auto clean after ... days
"""

class MachineData(db_client.Model):
    __tablename__ = "Machine Data"

    id              = Column("id", Integer, primary_key=True, autoincrement=True)
    deviceId        = Column("device_id", String(16), nullable=False)
    machineStatus   = Column("machine_status", Integer, nullable=False)
    actual          = Column("actual", Integer, nullable=False)
    runningNumber   = Column("runningNumber", Integer, nullable=False)
    timestamp       = Column("timestamp", Integer)
    temperature     = Column("temperature", Float)
    humidity        = Column("humidity", Float)
    isChanging      = Column("isChanging", Boolean)


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

