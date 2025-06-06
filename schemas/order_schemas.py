from typing import List, Optional
from pydantic import BaseModel

class CakeCreate(BaseModel):
    name: str
    weight: int
    price: float

class CakeOrderCreate(BaseModel):
    cake_name: str
    weight: int
    factory_id: Optional[int] = None
    quantity: int

class CakeOut(BaseModel):
    id: int
    name: str
    weight: int
    price: float

    class Config:
        orm_mode = True

class SingleCakeOrder(BaseModel):
    cake_name: str
    weight: int
    quantity: int
    factory_id: Optional[int] = None

class MultiCakeOrderCreate(BaseModel):
    orders: List[SingleCakeOrder]

class CakeOrderOut(BaseModel):
    id: int
    order_id: int
    cake_name: str
    weight: int
    price: float
    quantity: int
    order_status: str
    factory_id: Optional[int]
    user_id: int

    class Config:
        orm_mode = True

class OrderOut(BaseModel):
    order_id: int
    created_at: Optional[str]
    status: str
    cakes: List[CakeOrderOut]

    class Config:
        orm_mode = True