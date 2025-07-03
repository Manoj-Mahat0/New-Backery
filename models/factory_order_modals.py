from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from db import Base

class CakeOrder(Base):
    __tablename__ = "cake_orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    factory_id = Column(Integer, ForeignKey("users.id"))  # FACTORY is also a user

    cake_name = Column(String(100))  # ✅ Specify VARCHAR length
    weight = Column(Integer)
    price = Column(Float)

    user = relationship("User", foreign_keys=[user_id], back_populates="orders", lazy="joined")
    factory = relationship("User", foreign_keys=[factory_id], lazy="joined")
