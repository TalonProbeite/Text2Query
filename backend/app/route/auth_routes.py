from fastapi import APIRouter, Depends, HTTPException , Response
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from datetime import datetime, timezone, timedelta

from app.schemas.auth import AuthResponse , UserLogIn , UserRegister 
from app.db.database import get_db
from app.repositories.users_repo import UserRepository
from app.core.exceptions import InvalidPassword , UserNotFound ,UserBannedError , JWTTokenDecodeError , JWTTokenGenerateError, UserAlreadyExists
from app.utils.jwt import encode_jwt

router = APIRouter(prefix="/auth", tags=["Auth"])



@router.post("/login", response_model=AuthResponse)
async def login(user_data:UserLogIn ,response: Response, db:AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    try:
        user_model = await repo.user_login(**user_data.model_dump())
        token = encode_jwt({
            "sub": str(user_model.id),
            "email": user_model.email,
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=8)
        })

        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=60 * 60 * 8
        )
        return AuthResponse(
            id=user_model.id,
            name=user_model.name,
            email=user_model.email,
            plan=user_model.plan
        )
    except InvalidPassword as e:
        logger.info(f"Invalid password:{e.__cause__}")
        raise HTTPException(status_code=401, 
                            detail="incorrect email or password")
    except UserNotFound as e:
        logger.info(f"User not found:{e.__cause__}")
        raise HTTPException(status_code=401, 
                            detail="incorrect email or password")
    except UserBannedError as e:
        logger.info(f"User is banned:{e.__cause__}")
        raise HTTPException(status_code=403, 
                            detail="Access denied!")
    except (JWTTokenGenerateError, JWTTokenDecodeError):
        logger.error("Error creating jwt token")
        raise HTTPException(status_code=500, detail="Internal server error")


    
@router.post("/signup", response_model=AuthResponse)
async def signup(user_data:UserRegister,response: Response, db:AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    try:
        user_model = await repo.user_registration(**user_data.model_dump())
        token = encode_jwt({
            "sub": str(user_model.id),
            "email": user_model.email,
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=8)
        })

        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=60 * 60 * 8
        )

        return AuthResponse(
            id=user_model.id,
            name=user_model.name,
            email=user_model.email,
            plan=user_model.plan
        )
    except UserAlreadyExists as e:
        logger.info(f"Email already exists:{e.__cause__}")
        raise HTTPException(status_code=400, detail="Registration failed")
    except (JWTTokenGenerateError, JWTTokenDecodeError):
        logger.error("Error creating jwt token")
        raise HTTPException(status_code=500, detail="Internal server error")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
        
