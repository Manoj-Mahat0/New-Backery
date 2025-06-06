from pydantic import BaseModel

class StoreCreate(BaseModel):
    name: str
    main_store_id: int

class FactoryCreate(BaseModel):
    name: str
    main_store_id: int

class MainStoreCreate(BaseModel):
    name: str
    location: str
