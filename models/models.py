from sqlalchemy import Column, Integer, String, ForeignKey
from db import Base

class MainStore(Base):
    __tablename__ = "main_store"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    location = Column(String)

class Store(Base):
    __tablename__ = "stores"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    main_store_id = Column(Integer, ForeignKey("main_store.id"))

class Factory(Base):
    __tablename__ = "factories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    main_store_id = Column(Integer, ForeignKey("main_store.id"))
