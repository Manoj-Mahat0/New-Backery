from pydantic import BaseModel

class SignupSchema(BaseModel):
    name: str
    phone_number: str
    email: str
    address: str
    dob: str
    role: str

class LoginSchema(BaseModel):
    phone_number: str
    dob: str

class UserOut(BaseModel):
    id: int
    name: str
    phone_number: str
    email: str
    address: str
    role: str

    class Config:
        orm_mode = True