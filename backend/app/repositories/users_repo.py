from sqlalchemy.ext.asyncio import AsyncSession
from typing import  Optional
from sqlalchemy import select

from app.models.users import User
from app.utils.pas_hashing import get_hash_pass , match_password
from app.core.exceptions import InvalidPassword , UserAlreadyExists , UserNotFound , UserBannedError




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
