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

    def __init__(self, connection_data: dict, ) -> None:
        self.dialect = connection_data.get("dialect")
        self.connection_data = connection_data
        self.engine = None

    def _build_connection_string(self) -> str:
        driver = DRIVERS.get(self.dialect)
        if not driver:
            raise DBConnectionError(f"Unsupported db type: {self.dialect}")
        
        d = self.connection_data
        return f"{driver}://{d['db_username']}:{d['password']}@{d['host']}:{d['port']}/{d['database_name']}"

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

    async def get_sctruct(self)->list:
        extract_query = {
            "postgresql":"""SELECT 
                                cols.table_name, 
                                cols.column_name, 
                                cols.data_type,
                                (SELECT count(*) > 0 
                                FROM information_schema.key_column_usage kcu 
                                WHERE kcu.table_name = cols.table_name 
                                AND kcu.column_name = cols.column_name) as is_primary_or_foreign
                            FROM 
                                information_schema.columns cols
                            WHERE 
                                cols.table_schema = 'public'
                            ORDER BY 
                                cols.table_name, cols.ordinal_position;""",
            "mariadb":f"""SELECT 
                            c.TABLE_NAME, 
                            c.COLUMN_NAME, 
                            c.DATA_TYPE, 
                            c.COLUMN_KEY,
                            k.REFERENCED_TABLE_NAME, 
                            k.REFERENCED_COLUMN_NAME
                        FROM 
                            information_schema.columns c
                        LEFT JOIN 
                            information_schema.KEY_COLUMN_USAGE k 
                            ON c.TABLE_SCHEMA = k.TABLE_SCHEMA 
                            AND c.TABLE_NAME = k.TABLE_NAME 
                            AND c.COLUMN_NAME = k.COLUMN_NAME
                        WHERE 
                            c.TABLE_SCHEMA = '{self.connection_data['db_username']}'
                        ORDER BY 
                            c.TABLE_NAME, c.ORDINAL_POSITION;""",
            "mysql":f"""SELECT 
                            c.TABLE_NAME, 
                            c.COLUMN_NAME, 
                            c.DATA_TYPE, 
                            c.COLUMN_KEY,
                            k.REFERENCED_TABLE_NAME, 
                            k.REFERENCED_COLUMN_NAME
                        FROM 
                            information_schema.columns c
                        LEFT JOIN 
                            information_schema.KEY_COLUMN_USAGE k 
                            ON c.TABLE_SCHEMA = k.TABLE_SCHEMA 
                            AND c.TABLE_NAME = k.TABLE_NAME 
                            AND c.COLUMN_NAME = k.COLUMN_NAME
                        WHERE 
                            c.TABLE_SCHEMA = '{self.connection_data['db_username']}'
                        ORDER BY 
                            c.TABLE_NAME, c.ORDINAL_POSITION;"""
        }
            
        if not self.engine:
            raise DBConnectionError("No active connection")
        try:
            async with AsyncSession(self.engine) as session:
                result = await session.execute(text(extract_query[self.dialect]))
                tables = []
                tb = set()
                for row in result.mappings().all():
                    if row["table_name"] not in tb:
                        tables.append({"name":row["table_name"], "colums":[{"name":row["column_name"], "type":row['data_type'], "is_primary_or_foreign":row["is_primary_or_foreign"]}]})
                        tb.add(row["table_name"])
                    else:
                        tables[-1]["colums"].append({"name":row["column_name"], "type":row['data_type'], "is_primary_or_foreign":row["is_primary_or_foreign"]})
                return tables
        except SQLAlchemyError as e:
            raise DBQueryError() from e
   