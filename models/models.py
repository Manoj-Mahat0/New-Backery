from sqlalchemy import Column, Integer, String, ForeignKey
from db import Base

class MainStore(Base):
    __tablename__ = "main_store"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)      # ✅ Add length
    location = Column(String(255), nullable=True)   # ✅ Add length


class Store(Base):
    __tablename__ = "stores"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)             # ✅ Add length
    main_store_id = Column(Integer, ForeignKey("main_store.id"), nullable=False)


class Factory(Base):
    __tablename__ = "factories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)             # ✅ Add length
    main_store_id = Column(Integer, ForeignKey("main_store.id"), nullable=False)
