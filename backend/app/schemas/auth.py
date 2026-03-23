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


