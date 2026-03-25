from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.schemas.auth import AuthResponse , UserLogIn , UserRegister
from app.db.database import get_db
from app.repositories.users_repo import UserRepository
from app.core.exceptions import InvalidPassword , UserNotFound ,UserBannedError , JWTTokenDecodeError , JWTTokenGenerateError
from app.utils.jwt import encode_jwt

router = APIRouter(prefix="/auth", tags=["Auth"])



@router.post("/login/", response_model=AuthResponse)
async def login(user_data:UserLogIn, db:AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    try:
        user_model = await repo.user_login(**user_data.model_dump())
        user_response = UserResponse.model_validate(user_model)
        token = encode_jwt({"id": user_response.id, "email": user_response.email})
        return AuthResponse(
            jwt_token=token,
            name=user_response.name,
            email=user_response.email,
            plan=user_response.plan
        )

        return user
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


    