from sqlalchemy import Column, Integer, String, Float
from app import db
"""
Cached database, when sent successfully, clear record
"""
class UnsyncedMachineData(db.Model):
    __tablename__ = "Unsynced Machine Data"

    id              = Column("id", Integer, primary_key=True, autoincrement=True)
    deviceId        = Column("device_id", String(16), nullable=False)
    machineStatus   = Column("machine_status", Integer, nullable=False)
    actual          = Column("actual", Integer, nullable=False)
    runningNumber   = Column("runningNumber", Integer, nullable=False)
    timestamp       = Column("timestamp", Integer)
    temperature     = Column("temperature", Float)
    humidity        = Column("humidity", Float)
