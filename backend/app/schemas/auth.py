from pydantic import Field, BaseModel, ConfigDict , EmailStr
from typing import Optional
from datetime import datetime


class UserRegister(BaseModel):
    name:str
    password :str
    email:EmailStr

class UserLogIn(BaseModel):
    email:EmailStr
    password:str


class AuthResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    jwt_token:str
    name: str
    email: str
    plan: str
