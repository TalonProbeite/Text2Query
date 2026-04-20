from fastapi import APIRouter, Depends, HTTPException , Request
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
import json 

from app.db.database import get_db
from app.services.llm_service import LlmService
from app.core.config import settings
from app.schemas.sql import SqlResponse , UserPrompt
from app.core.exceptions import NotSqlPromt
from app.core.dependencies import get_llm_service
from app.repositories.history_repo import QueryHistoryRepository
from app.db.redis import redis 

router = APIRouter(prefix="/sql", tags=["SQL"])


@router.post(path="/get_sql")
async def get_sql(user_data: UserPrompt , 
                  request:Request, 
                  llm: LlmService = Depends(get_llm_service),
                  db:AsyncSession = Depends(get_db)):
    try:
        raw = await redis.get(f"session:user_{request.state.user_id}")
        if raw:
            db_struct = json.loads(raw)
        else:
            db_struct = ""
        resp = await llm.get_query(input_text=user_data.prompt, sql_type=user_data.sql_type , full_context=db_struct)
        
        is_danger =  llm.is_dangerous(resp)
        if is_danger:
            resp = resp.replace("danger", "")
        repo = QueryHistoryRepository(db)
        await repo.add_query(request.state.user_id ,user_data.prompt, resp,is_danger, user_data.sql_type)
        return SqlResponse(query=resp , is_danger=is_danger)
    except NotSqlPromt as e:
        logger.info(f"The user entered a promt not related to sql:{e.__cause__}")
        raise HTTPException(status_code=400 , detail="The query is not related to sql!")
    except Exception as e:
        logger.warning(f"Error when generating sql query:{e}")
        raise HTTPException(status_code=502, detail="Failed to generate response")
    
