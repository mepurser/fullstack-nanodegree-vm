from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, EquipCategory, EquipBrand

#app = Flask(__name__)

engine = create_engine('sqlite:///pv_equipment.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

def addItem(entry):
	session.add(entry)
	session.commit()

# initial equipment category data
equipCat1 = EquipCategory(name="PV Panels")
addItem(equipCat1)

equipCat3 = EquipCategory(name="Inverters")
addItem(equipCat3)

equipCat2 = EquipCategory(name="Bracketing")
addItem(equipCat2)

# initial brand data
equipBrand1 = EquipBrand(name="Sunpower", category_id=1, description='Sunpower-made PV panels')
addItem(equipBrand1)

equipBrand2 = EquipBrand(name="LG", category_id=1, description='LG-made PV panels')
addItem(equipBrand2)

equipBrand3 = EquipBrand(name="Trina", category_id=1, description='Trina-made PV panels')
addItem(equipBrand3)

equipBrand4 = EquipBrand(name="Sunnyboy", category_id=2, description='Sunnyboy string inverters')
addItem(equipBrand4)

equipBrand5 = EquipBrand(name="Enphase", category_id=2, description='Enphase micro-inverters')
addItem(equipBrand5)

equipBrand6 = EquipBrand(name="LG", category_id=2, description='LG string inverters')
addItem(equipBrand6)

equipBrand7 = EquipBrand(name="Snap n rack", category_id=3, description='Sunrun-made rails')
addItem(equipBrand7)

equipBrand8 = EquipBrand(name="Zep", category_id=3, description='Solarcity-made rails')
addItem(equipBrand8)

equipBrand9 = EquipBrand(name="Railless", category_id=3, description='SunEdison-made railless system')
addItem(equipBrand9)


print("since empty, added initial equipment/brands!")