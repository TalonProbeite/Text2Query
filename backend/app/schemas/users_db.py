from pydantic import BaseModel  , Field



class DbConnectCreat(BaseModel):
    host:str
    port:int
    db_name:str
    username:str
    password:str
    db_type:str



class DbExecute(DbConnectCreat):
    query:str
