from fastapi import APIRouter, Depends, HTTPException 
from loguru import logger

from app.schemas.users_db import DbConnectCreat , DbExecute
from app.services.connection_db_service import ConnectionDbService
from app.core.exceptions import DBConnectionError, DBQueryError

router = APIRouter(prefix="/user_db", tags=["UserDatabases"])

@router.post("/try_connect")
async def connect_db(db_data:DbConnectCreat):
    try:
        service = ConnectionDbService(db_data.model_dump())
        await service.connect()
        return {"success":True}
    except (DBConnectionError, DBQueryError) as e:
        logger.info(f"Connection to user database failed: {e}")
        raise HTTPException(status_code=400 , detail="Connection to user database failed")
    except Exception as e:
        logger.info(f'Error connecting to user database: {e}')
        raise HTTPException(status_code=500)
    finally:
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
