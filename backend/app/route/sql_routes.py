from fastapi import APIRouter, Depends, HTTPException , Response
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.db.database import get_db
from app.services.llm_service import LlmService
from app.core.config import settings
from app.schemas.sql import SqlResponse , UserPrompt
from app.core.exceptions import NotSqlPromt
from app.core.dependencies import get_llm_service

router = APIRouter(prefix="/sql", tags=["SQL"])


@router.post(path="/get_sql")
async def get_sql(user_data: UserPrompt , 
                  response:Response, 
                  llm: LlmService = Depends(get_llm_service),
                  db:AsyncSession = Depends(get_db)):
    try:
        resp = await llm.get_query(user_data.prompt, user_data.sql_type)
        
        is_danger =  llm.is_dangerous(resp)
        if is_danger:
            resp.replace("danger", "")

        return SqlResponse(query=resp , is_danger=is_danger)
    except NotSqlPromt as e:
        logger.info(f"The user entered a promt not related to sql:{e}")
        raise HTTPException(status_code=400 , detail="The query is not related to sql!")
    except Exception as e:
        logger.warning(f"Error when generating sql query:{e}")
        raise HTTPException(status_code=502, detail="Failed to generate response")
    
