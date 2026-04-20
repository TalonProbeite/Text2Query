from fastapi import APIRouter, Depends, HTTPException , Response , Request
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from datetime import datetime, timezone, timedelta
from fastapi_mail import  MessageSchema , MessageType

from app.schemas.auth import AuthResponse , UserLogIn , UserRegister , VerificationResponse
from app.db.database import get_db
from app.repositories.users_repo import UserRepository
from app.core.exceptions import InvalidPassword , UserNotFound ,UserBannedError , JWTTokenDecodeError , JWTTokenGenerateError, UserAlreadyExists , IncorrectVerificationTokenError , VerificationTokenExpireError
from app.utils.jwt import encode_jwt
from app.utils.mail_utils import send_email_async , generate_verification_code , get_html_verify_message

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
async def signup(user_data:UserRegister,db:AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    try:
        user_model = await repo.user_registration(**user_data.model_dump())

        token = generate_verification_code()
        html = get_html_verify_message(token)
        await repo.add_verifi_token(user_id=user_model.id, token=token)
        await send_email_async(subject="SqlCraft | Подтверждение регистрации", email_to=user_model.email , body=html)
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
        logger.exception(f"Unexpected error: {e.__cause__}")
        raise HTTPException(status_code=500, detail="Internal server error")
        


@router.post("/logout")
async def logout(response: Response):
    try:
        response.delete_cookie(
            key="access_token",
            path="/"
        )
        return {"success":True}
    except Exception as e:
        logger.info(f"error on exit:{e.__cause__}") 
        return {"success":False}
    



@router.get("/me")
async def is_logged(request: Request, db: AsyncSession = Depends(get_db)):
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        return {"is_logged": False}
    
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        return {"is_logged": False}
    
    return {
        "is_logged": True,
        "name": user.name,
        "plan": user.plan
    }

@router.post("/ver_conf" , response_model=AuthResponse)
async def verify_mail(user_data: VerificationResponse , response:Response, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    try:
        user = await repo.check_verifi_token(user_id=user_data.id, token=user_data.token)
        if  user:
            if not user.email == user_data.email:
                raise UserNotFound()
            await repo.set_verefi(user_id=user_data.id)
            token = encode_jwt({
            "sub": str(user.id),
            "email": user.email,
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
            id=user.id,
            name=user.name,
            email=user.email,
            plan=user.plan
        )
        else:
            logger.info("Invalid verification code!")
            raise HTTPException(status_code=400, detail="Invalid verification code!")
    except UserNotFound as e:
        logger.warning(f"Invalid id from user's schema:{e.__cause__}")
        raise HTTPException(status_code=400)
    except UserBannedError as e:
        logger.info(f"Access denied:{e.__cause__}")
        raise HTTPException(status_code=403 , detail="Access denied")
    except (VerificationTokenExpireError , IncorrectVerificationTokenError) as e:
        logger.info("Invalid verification code!")
        raise HTTPException(status_code=400, detail="The token's lifetime has expired or the code is incorrect!")
    except Exception as e:
        logger.exception(f"Unknown error when trying to confirm verification: {e.__cause__}")
        raise HTTPException(status_code=500)
    

@router.post("/send_code")
async def send_ver_token(user_data: VerificationResponse , db: AsyncSession = Depends(get_db)):
    pass