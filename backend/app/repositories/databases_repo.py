from sqlalchemy.ext.asyncio import AsyncSession
from typing import  Optional , List
from sqlalchemy import select

from app.models.databases import Database
from app.core.exceptions import *


class DatabaseRepository:

    def __init__(self, db:AsyncSession) -> None:
        self.db  = db


    async def get_by_id(self, db_id)-> Optional[Database]:
        result = await self.db.execute(select(Database).where(Database.id == db_id))
        return result.scalar_one_or_none()
    
    async def get_user_dbs(self, user_id,db:AsyncSession)->List[Database]:
        result = await self.db.execute(select(Database).where(Database.user_id == user_id))
        return result.scalars().all()