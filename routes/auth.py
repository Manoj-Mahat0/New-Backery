from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt
from db import get_db
from models.user import User
from schemas.user import SignupSchema, LoginSchema

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "supersecretkey"  # Change in prod
ALGORITHM = "HS256"

def hash_dob(dob: str):
    return pwd_context.hash(dob)

def verify_dob(plain: str, hashed: str):
    return pwd_context.verify(plain, hashed)

@router.post("/signup")
def signup(data: SignupSchema, db: Session = Depends(get_db)):
    existing = db.query(User).filter(
        (User.phone_number == data.phone_number) | (User.email == data.email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Phone or Email already registered")
    
    hashed_dob = hash_dob(data.dob)
    new_user = User(**data.dict(exclude={"dob"}), dob=hashed_dob)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "Signup successful", "user": new_user.name, "role": new_user.role}


@router.post("/login")
def login(data: LoginSchema, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone_number == data.phone_number).first()
    if not user or not verify_dob(data.dob, user.dob):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token_data = {
        "sub": user.phone_number,
        "role": user.role,
        "name": user.name
    }
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "user": user.name, "role": user.role}
