import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name =  Column(String(80), nullable=False)
    email = Column(String(80), nullable=False)
    picture = Column(String(80))

class EquipCategory(Base):
    __tablename__ = 'equip_category'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship(User)

class EquipBrand(Base):
    __tablename__ = 'equip_brand'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    description = Column(String(250))
    subcategory = Column(String(250))
    category_id = Column(Integer, ForeignKey('equip_category.id'))
    category = relationship(EquipCategory)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship(User)

engine = create_engine('sqlite:///pv_equipment.db')

Base.metadata.create_all(engine)