from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone_number = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    address = Column(String)
    dob = Column(String, nullable=False)  # Stored as hashed password
    role = Column(String, nullable=False)  # MAIN_STORE / STORE / FACTORY
    orders = relationship("CakeOrder", back_populates="user", foreign_keys="[CakeOrder.user_id]")
