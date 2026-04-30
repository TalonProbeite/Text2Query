from fastapi import APIRouter, Depends, HTTPException , Request
from loguru import logger
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import inspect 
from datetime import datetime , timezone

from app.schemas.users_db import DbConnectCreat , DbExecute , DbConnectResponse , StartSessionDb
from app.services.connection_db_service import ConnectionDbService 
from app.core.exceptions import DBConnectionError, DBQueryError
from app.db.redis import redis
from app.repositories.databases_repo import DatabaseRepository
from app.db.database import get_db
from app.utils.crypto_utils import CryptoUtils

router = APIRouter(prefix="/user_db", tags=["UserDatabases"])

@router.post("/try_connect")
async def connect_db(db_data:DbConnectCreat, request: Request , db:AsyncSession= Depends(get_db)):
    try:
        service = ConnectionDbService(db_data.model_dump())
        await service.connect()
        db_struct = await service.get_sctruct()
        crypto_util = CryptoUtils()
        repo = DatabaseRepository(db)
        password = crypto_util.encrypt_password(db_data.password)
        data = db_data.model_dump()
        data.pop("password")
        user_db = await repo.create_users_db(user_id=request.state.user_id,**data)
        await redis.set(f"session:user_{request.state.user_id}:db_{user_db.id}", json.dumps({
                                                                        "id": user_db.id,
                                                                        "db_alias": user_db.database_alias,
                                                                        "host": user_db.host,
                                                                        "port": user_db.port,
                                                                        "dialect": user_db.dialect,
                                                                        "db_name": user_db.database_name,
                                                                        "username": user_db.db_username,
                                                                        "password_encrypted": password,
                                                                        "struct": json.dumps(db_struct),
                                                                        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")}), ex=28800)
        
        return DbConnectResponse(id= user_db.id,
                                 db_alias=user_db.database_alias,
                                 db_name=user_db.database_name,
                                 is_active=True)
    except (DBConnectionError, DBQueryError) as e:
        logger.exception(f"Connection to user database failed: {e.__cause__}")
        raise HTTPException(status_code=400 , detail="Connection to user database failed")
    except Exception as e:
        logger.exception(f'Error connecting to user database:')
        raise HTTPException(status_code=500)
    finally:
        if service and service.engine:
            await service.disconnect()

    
@router.post("/execute_query")
async def execute_query(db_data:DbExecute, request: Request):
    try:
        raw = await redis.get(f"session:user_{request.state.user_id}:db_{db_data.id}")
        if not raw:
            raise HTTPException(status_code=400, detail="Database not connected")
            
        data = json.loads(raw)
        crypto_util = CryptoUtils()
        password = crypto_util.decrypt_password(data["password_encrypted"])

        connection_data = {
            "db_username": data["username"],
            "password": password,
            "host": data["host"],
            "port": data["port"],
            "database_name": data["db_name"],
            "dialect": data["dialect"]
        }

        service = ConnectionDbService(connection_data)
        await service.connect()
        result = await service.execute_query(db_data.query)
        return result
    except (DBConnectionError, DBQueryError) as e:
        logger.info(f"Connection to user database failed: {e.__cause__}")
        raise HTTPException(status_code=400 , detail="Connection to user database failed")
    except HTTPException:
        raise
    except Exception as e:
        logger.info(f'Error connecting to user database: {e.__cause__}')
        raise HTTPException(status_code=500)   
    finally:
        if service and service.engine:
            await service.disconnect()


@router.get("/get_users_db")
async def get_users_db(request: Request , db:AsyncSession= Depends(get_db)):
    repo = DatabaseRepository(db)
    try:
        user_id = request.state.user_id
        dbs = await repo.get_user_dbs(user_id=user_id)
        result = []
        for el in dbs:
            db_conf = await redis.get(f"session:user_{request.state.user_id}:db_{el.id}")
            if db_conf:
                is_active = True
            else:
                is_active = False

            result.append(DbConnectResponse(id=el.id , db_alias=el.database_alias ,db_name=el.database_name ,is_active=is_active))
        return result
    except Exception as e:
        logger.info(f'Error connecting to user database: {e.__cause__}')
        raise HTTPException(status_code=500) 
    

@router.post("/start_session")
async def start_session(user_credentials:StartSessionDb , request:Request ,db:AsyncSession= Depends(get_db)):
    repo = DatabaseRepository(db)
    try:
        db_config = await repo.get_user_db(request.state.user_id , user_credentials.id)
        if not db_config:
            logger.warning("Database not found!")
            raise HTTPException(status_code=404, detail="Database not found!")
        db_dict = {c.key: getattr(db_config, c.key) for c in inspect(db_config).mapper.column_attrs} 
        db_dict |= {"password":user_credentials.password}
        service = ConnectionDbService(db_dict)
        await service.connect()
        db_struct = await service.get_sctruct()
        crypto_util = CryptoUtils()
        password = crypto_util.encrypt_password(user_credentials.password)
        await redis.set(f"session:user_{request.state.user_id}:db_{db_config.id}", json.dumps({
                                                                        "id": db_config.id,
                                                                        "db_alias": db_config.database_alias,
                                                                        "host": db_config.host,
                                                                        "port": db_config.port,
                                                                        "dialect": db_config.dialect,
                                                                        "db_name": db_config.database_name,
                                                                        "username": db_config.db_username,
                                                                        "password_encrypted": password,
                                                                        "struct": json.dumps(db_struct),
                                                                        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")}), ex=28800)
    
        return DbConnectResponse(id=db_config.id, db_alias=db_config.database_alias, db_name=db_config.database_name,is_active=True)
    except HTTPException:
        raise
    except (DBConnectionError, DBQueryError) as e:
        logger.info(f"Connection to user database failed: {e.__cause__}")
        raise HTTPException(status_code=400 , detail="Connection to user database failed")
    except Exception as e:
        logger.exception(f'Error connecting to user database: {e.__cause__}')
        raise HTTPException(status_code=500)   
    finally:
        if service and service.engine:
            await service.disconnect()



@router.delete("/delete_db")
async def  delete_user_db(db_id:int , request:Request ,db:AsyncSession= Depends(get_db)):
    repo = DatabaseRepository(db=db)
    try:
        user_db = await repo.get_by_id(db_id)
        if  not user_db:
            logger.info("User database not found")
            raise HTTPException(status_code=404, detail="Database not found!")
        if user_db.user_id != request.state.user_id:
            logger.warning(f"User id does not match the id from the request! User: id from request{request.state.user_id}")
            raise HTTPException(status_code=404 , detail="Database not found!")
        result = await repo.delete_by_id(db_id=db_id)
        if result:
            return {"success": True}
        else:
            return{"success": False}
    except  HTTPException :
        raise
    except Exception as e:
        logger.exception(f'Error when deleting user database: {e.__cause__}')
        raise HTTPException(status_code=500) 