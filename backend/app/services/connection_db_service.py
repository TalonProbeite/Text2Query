from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app.core.exceptions import DBConnectionError, DBQueryError

DRIVERS = {
    "postgresql": "postgresql+asyncpg",
    "mysql":      "mysql+aiomysql",
    "mariadb":    "mysql+aiomysql",
}

class ConnectionDbService:

    def __init__(self, connection_data: dict, db_type: str) -> None:
        self.dialect = db_type
        self.connection_data = connection_data
        self.engine = None

    def _build_connection_string(self) -> str:
        driver = DRIVERS.get(self.dialect)
        if not driver:
            raise DBConnectionError(f"Unsupported db type: {self.dialect}")
        
        d = self.connection_data
        return f"{driver}://{d['username']}:{d['password']}@{d['host']}:{d['port']}/{d['db_name']}"

    async def connect(self) -> None:
        try:
            connection_string = self._build_connection_string()
            self.engine = create_async_engine(
                connection_string,
                connect_args={"timeout": 10},
                pool_timeout=10,
            )
            
            async with self.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        except SQLAlchemyError as e:
            raise DBConnectionError() from e

    async def execute_query(self, query: str) -> list[dict]:
        if not self.engine:
            raise DBConnectionError("No active connection")
        try:
            async with AsyncSession(self.engine) as session:
                result = await session.execute(text(query))
                return [dict(row) for row in result.mappings().all()]
        except SQLAlchemyError as e:
            raise DBQueryError() from e

    async def disconnect(self) -> None:
        if self.engine:
            await self.engine.dispose()
            self.engine = None
    
            
   