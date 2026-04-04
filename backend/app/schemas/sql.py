from pydantic import BaseModel  , Field




class SqlResponse(BaseModel):
        query:str = Field(... , min_length=10 , max_length=300)
        is_danger:bool


class UserPrompt(BaseModel):
        prompt :str = Field(... , min_length=10 , max_length=300)
        sql_type:str = Field(...  , max_length=10)