from pydantic import BaseModel  , Field




class SqlResponse(BaseModel):
        query:str = Field(... , min_length=5 , max_length=800)
        is_danger:bool


class UserPrompt(BaseModel):
        prompt :str = Field(... , min_length=5 , max_length=500)
        sql_type:str = Field(...  , max_length=10)