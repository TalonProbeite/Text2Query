from sqlalchemy.ext.asyncio import AsyncSession
from typing import  Optional , List
from sqlalchemy import select , delete

from app.models.databases import Database
from app.core.exceptions import *


class DatabaseRepository:

    def __init__(self, db:AsyncSession) -> None:
        self.db  = db


    async def get_by_id(self, db_id)-> Optional[Database]:
        result = await self.db.execute(select(Database).where(Database.id == db_id))
        return result.scalar_one_or_none()
    
    async def get_user_dbs(self, user_id)->List[Database]:
        result = await self.db.execute(select(Database).where(Database.user_id == user_id))
        return result.scalars().all()
    
    async def create_users_db(self, user_id:int , dialect: str  ,
                             database_alias:str , host:str , port:int ,
                             database_name:str, db_username:str , ssl:bool)->Database:
        
        user_db = Database(dialect= dialect,
                      database_alias=database_alias,
                      host=host,
                      port=port,
                      database_name=database_name,
                      db_username=db_username,
                      ssl=ssl,
                      user_id=user_id)
        
        self.db.add(user_db)
        await self.db.commit()
        await self.db.refresh(user_db)
        return user_db
    
    async def delete_by_id(self, db_id):
        result = await self.db.execute(delete(Database).where(Database.id == db_id))
        await self.db.commit()
        return result
    
    async def get_user_db(self, user_id:int , db_id:int)->Database:
        result  = await self.db.execute(select(Database).where(Database.id == db_id and Database.user_id == user_id))
        return result.scalar_one_or_none()