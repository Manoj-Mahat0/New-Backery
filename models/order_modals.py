from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from db import Base
from datetime import datetime

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="PLACED")

    user = relationship("User")
    cake_orders = relationship("CakeOrder", back_populates="order")

class CakeOrder(Base):
    __tablename__ = "cake_orders"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))  # Link to Order
    user_id = Column(Integer, ForeignKey("users.id"))
    factory_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    cake_name = Column(String)
    weight = Column(Integer)
    price = Column(Float)
    quantity = Column(Integer, nullable=False, default=1)
    order_status = Column(String, default="PLACED")

    order = relationship("Order", back_populates="cake_orders")
    user = relationship("User", foreign_keys=[user_id], back_populates="orders", lazy="joined")
    factory = relationship("User", foreign_keys=[factory_id], lazy="joined")

class Cake(Base):
    __tablename__ = "cakes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    weight = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)

class DesignerCakeOrder(Base):
    __tablename__ = "designer_cake_orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    factory_id = Column(Integer, ForeignKey("users.id"))
    theme = Column(String, nullable=False)
    message_on_cake = Column(String)
    
    image_url = Column(String, nullable=True)         # ✅ optional
    print_image_url = Column(String, nullable=False)  # keep required or set to nullable=True if optional
    audio_url = Column(String, nullable=True)         # optional
    
    weight = Column(Float, nullable=False)            # ✅ float
    price = Column(Float, nullable=False)
    quantity = Column(Integer, default=1)
    order_status = Column(String, default="PLACED")

    user = relationship("User", foreign_keys=[user_id])
    factory = relationship("User", foreign_keys=[factory_id])
