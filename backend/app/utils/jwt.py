import jwt
from pathlib import Path

from app.core.exceptions import JWTTokenGenerateError , JWTTokenDecodeError
from app.core.config import settings


def encode_jwt(attributes:dict,
               private_key:str=settings.private_key,
               algorithm:str= settings.algorithm, 
                 )->str:
    try:
    
        jwt_token  = jwt.encode(attributes , private_key, algorithm)
        return jwt_token
    except Exception as e:
        raise JWTTokenGenerateError() from e
    

def decode_jwt(token:str,
               public_key:str=settings.public_key,  
               algorithm:str = settings.algorithm ,
               )->dict:

    try:
        return jwt.decode(token, public_key, algorithms=[algorithm])
    except Exception as e:
        raise JWTTokenDecodeError()  from e