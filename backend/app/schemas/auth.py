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
    

    id: int
    name: str
    email: EmailStr
    plan: str
    is_verified:bool


class VerificationResponse(BaseModel):

    id: int
    email: EmailStr
    token: str


class GetToken(BaseModel):

    id:int
    email:EmailStr

class SetMail(BaseModel):

    id:int
    email:EmailStr
    new_email:EmailStr