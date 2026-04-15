from fastapi import APIRouter, Depends, HTTPException , Request
from loguru import logger
import json

from app.schemas.users_db import DbConnectCreat , DbExecute
from app.services.connection_db_service import ConnectionDbService
from app.core.exceptions import DBConnectionError, DBQueryError
from app.db.redis import redis

router = APIRouter(prefix="/user_db", tags=["UserDatabases"])

@router.post("/try_connect")
async def connect_db(db_data:DbConnectCreat, request: Request):
    try:
        service = ConnectionDbService(db_data.model_dump())
        await service.connect()
        db_data = await service.get_sctruct()
        await redis.set(f"session:user_{request.state.user_id}",  json.dumps(db_data), ex=28800)
        return {"success":True}
    except (DBConnectionError, DBQueryError) as e:
        logger.info(f"Connection to user database failed: {e.__cause__}")
        raise HTTPException(status_code=400 , detail="Connection to user database failed")
    except Exception as e:
        logger.exception(f'Error connecting to user database:')
        raise HTTPException(status_code=500)
    finally:
        if service.engine:
            await service.disconnect()

    
@router.post("/execute_query")
async def execute_query(db_data:DbExecute):
    try:
        data = db_data.model_dump()
        service = ConnectionDbService(data)
        await service.connect()
        result = await service.execute_query(data.get("query"))
        return result
    except (DBConnectionError, DBQueryError) as e:
        logger.info(f"Connection to user database failed: {e}")
        raise HTTPException(status_code=400 , detail="Connection to user database failed")
    except Exception as e:
        logger.info(f'Error connecting to user database: {e}')
        raise HTTPException(status_code=500)   
    finally:
        await service.disconnect()
