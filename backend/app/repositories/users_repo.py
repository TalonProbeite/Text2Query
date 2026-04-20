from sqlalchemy.ext.asyncio import AsyncSession
from typing import  Optional
from sqlalchemy import select
from datetime import datetime , timezone , timedelta

from app.models.users import User
from app.utils.pas_hashing import get_hash_pass , match_password
from app.core.exceptions import InvalidPassword , UserAlreadyExists , UserNotFound , UserBannedError , VerificationTokenExpireError  , IncorrectVerificationTokenError




class UserRepository:

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, user_id)-> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    async def user_registration(self, name: str, email: str, password: str)-> User:
        if await self.get_by_email(email):
            raise UserAlreadyExists() 
        
        user = User(
            name = name,
            email = email,
            hashed_password = get_hash_pass(password)
        )

        try:
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            return  user
        except Exception as e:
            await self.db.rollback()
            raise e
        
    async def user_login(self, email: str, password: str)-> User:

        user = await self.get_by_email(email)

        if not user:    
            raise UserNotFound()
        if not user.is_active:
            raise UserBannedError()

        try:
            match_password(user.hashed_password, password)
        except Exception as e:
            raise InvalidPassword() from e

        return user
    
    async def add_verifi_token(self, user_id:int, 
                               token:str, 
                               token_exp_time:datetime=None)->User:
        if not token_exp_time:
            token_exp_time = datetime.now(timezone.utc) + timedelta(minutes=30)
            
        user = await self.get_by_id(user_id=user_id)

        if not user:    
            raise UserNotFound()
        if not user.is_active:
            raise UserBannedError()

        
        user.verification_token = token
        user.token_exp_time = token_exp_time
        await self.db.commit()
        await self.db.refresh(user) 

        return user
    
    async def check_verifi_token(self, user_id:int, 
                               token:str, )->User:
        
        user = await self.get_by_id(user_id=user_id)

        if not user:    
            raise UserNotFound()
        if not user.is_active:
            raise UserBannedError()
        if  datetime.now(timezone.utc) > user.token_exp_time:
            raise VerificationTokenExpireError()
        
        if user.verification_token == token:
            return user
        else:
            raise IncorrectVerificationTokenError()
    
    async def set_email(self , user_id, new_mail)->User:
        user = await self.get_by_id(user_id=user_id)
        mail = await self.get_by_email(new_mail)
        if not user:    
            raise UserNotFound()
        if not user.is_active:
            raise UserBannedError()
        if mail:
            raise UserAlreadyExists()
        
        try:
            user.email = new_mail
            await self.db.commit()
            await self.db.refresh(user) 
            return user
        except Exception as e:
            await self.db.rollback()
            raise e
        
    async def set_verefi(self, user_id)->User:
        user = await self.get_by_id(user_id)
        if user:
            user.is_verified = True
            await self.db.commit()
            await self.db.refresh(user) 
            return user
        else:
            raise UserNotFound()