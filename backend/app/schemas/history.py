from pydantic import BaseModel  , Field
from datetime import datetime, timezone


class QueryHistoryCreate(BaseModel):

    prompt:str
    query:str
    is_danger:bool
    dialect:str
    

class QueryHistoryRead(BaseModel):
    model_config = {"from_attributes": True} 
    
    prompt:str
    query:str
    is_danger:bool
    dialect:str
    created_at: datetime


