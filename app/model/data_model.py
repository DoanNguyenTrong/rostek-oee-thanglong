from sqlalchemy import MetaData
from sqlalchemy import Table, Column, Integer, String, Float
from sqlalchemy.dialects.mysql import TIMESTAMP
from sqlalchemy import create_engine
import logging
from sqlalchemy import insert

metadata_obj = MetaData()

MachineData = Table(
    "Machine Data",
    metadata_obj,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("device_id", String(16), nullable=False),
    Column("machine_status", Integer, nullable=False),
    Column("actual", Integer, nullable=False),
    Column("timestamp", TIMESTAMP),
    Column("temperature", Float),
    Column("humidity", Float)
)