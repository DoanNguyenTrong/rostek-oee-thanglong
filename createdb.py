from sqlalchemy import create_engine
from sqlalchemy import insert
from app.model.data_model import metadata_obj
from configure import GeneralConfig


engine = create_engine("sqlite:///"+ GeneralConfig.DATAFILE)
metadata_obj.create_all(engine)
print("Init Database Done !")

# stmt = insert(MachineData).values(device_id="test", nickname="Spongebob Squarepants")
# print(stmt)
# compiled = stmt.compile()
# print(compiled.params)