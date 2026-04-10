from fastapi import APIRouter, Depends, HTTPException , Request
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger


from app.db.database import get_db
from app.repositories.history_repo import  QueryHistoryRepository
from app.schemas.history import QueryHistoryCreate , QueryHistoryRead


router = APIRouter(prefix="/history", tags=["QueryHistori"])



# @router.post("/add_query", response_model=QueryHistoryRead)
# async def add_query(query_data: QueryHistoryCreate,
#                     request: Request,
#                     db:AsyncSession = Depends(get_db)):
#     repo = QueryHistoryRepository(db)
#     try:
#         result  = await repo.add_query(request.state.user_id,**query_data.model_dump())

#         return result
#     except Exception as e:
#         logger.info(f"Error when writing a request to the history: {e}")
#         raise HTTPException(status_code=500 , detail="Error adding request to history.")



@router.get("/get_history", response_model=list[QueryHistoryRead])
async def get_history(request: Request,db:AsyncSession = Depends(get_db)):
    repo = QueryHistoryRepository(db)
    try:
        result = await repo.get_user_history(user_id=request.state.user_id)
        return result
    except Exception as e:
        logger.info(f"Error reading history: {e}")
        raise HTTPException(status_code=500 , detail="Error reading history")
