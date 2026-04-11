from sqlalchemy.ext.asyncio import AsyncSession
from typing import  Optional
from sqlalchemy import select , delete

from app.models.history import QueryHistory


class QueryHistoryRepository:

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, history_id)-> Optional[QueryHistory]:
        result = await self.db.execute(select(QueryHistory).where(QueryHistory.id == history_id))
        return result.scalar_one_or_none()
    
    async def add_query(self, 
                        user_id: int, 
                        prompt: str, 
                        query: str, 
                        is_danger: bool, 
                        dialect: str):
        new_entry = QueryHistory(
            user_id=user_id,
            prompt=prompt,
            query=query,
            is_danger=is_danger,
            dialect=dialect
        )
        self.db.add(new_entry)
        await self.db.flush()

        
        subquery = (
            select(QueryHistory.id)
            .where(QueryHistory.user_id == user_id)
            .order_by(QueryHistory.created_at.desc())
            .limit(20)
            .subquery()
        )

        await self.db.execute(
            delete(QueryHistory).where(
                QueryHistory.user_id == user_id,
                QueryHistory.id.not_in(select(subquery))
            )
        )

        await self.db.commit()
        await self.db.refresh(new_entry)
        return new_entry
        
    async def get_user_history(self,user_id)->Optional[list[QueryHistory]]:
        result = await self.db.execute(select(QueryHistory).where(QueryHistory.user_id == user_id))
        return result.scalars().all()
