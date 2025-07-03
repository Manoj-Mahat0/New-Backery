from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone_number = Column(String(20), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    address = Column(String(255))
    dob = Column(String(50), nullable=False)  # Can adjust based on hashed format
    role = Column(String(50), nullable=False)  # Values like MAIN_STORE / STORE / FACTORY

    # Relationship with CakeOrder
    orders = relationship("CakeOrder", back_populates="user", foreign_keys="[CakeOrder.user_id]")
