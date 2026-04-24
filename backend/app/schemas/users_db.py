from pydantic import BaseModel  , Field



class DbConnectCreat(BaseModel):
    host:str
    port:int
    database_name:str
    database_alias:str
    db_username:str
    password:str
    dialect:str
    ssl:bool



class DbExecute(BaseModel):
    id:int
    query:str


class DbConnectResponse(BaseModel):
    id:int
    db_alias:str


class StartSessionDb(BaseModel):
    id:int
    password:str