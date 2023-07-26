from sqlalchemy import Table, Column, Integer, String, Float
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
    
class UnsyncedMachineData(Base):
    __tablename__ = "Unsynced Machine Data"

    id              = Column("id", Integer, primary_key=True, autoincrement=True)
    deviceId        = Column("device_id", String(16), nullable=False)
    machineStatus   = Column("machine_status", Integer, nullable=False)
    actual          = Column("actual", Integer, nullable=False)
    runningNumber   = Column("runningNumber", Integer, nullable=False)
    timestamp       = Column("timestamp", Integer)
    temperature     = Column("temperature", Float)
    humidity        = Column("humidity", Float)
