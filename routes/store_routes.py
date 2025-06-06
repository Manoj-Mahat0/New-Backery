from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db import get_db
from models.user import User
from typing import List
from schemas.user import UserOut

router = APIRouter()

# Get all stores
@router.get("/all-stores", response_model=List[UserOut])
def get_all_stores(db: Session = Depends(get_db)):
    return db.query(User).filter(User.role.in_(["STORE", "MAIN_STORE"])).all()


# Get all factories
@router.get("/all-factories", response_model=List[UserOut])
def get_all_factories(db: Session = Depends(get_db)):
    return db.query(User).filter(User.role == "FACTORY").all()
