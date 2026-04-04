from openai import AsyncOpenAI  
from openai.types.chat import ChatCompletion
import re


from app.core.exceptions import NotSqlPromt

class LlmService:

    def __init__(self, api_key: str, base_url: str = "https://api.groq.com/openai/v1", **kwargs) -> None:
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url, **kwargs)

    async def get_response(self, 
                           messages: list[dict], 
                           model: str = "llama-3.3-70b-versatile", 
                           **kwargs) -> ChatCompletion:
    
        response: ChatCompletion = await self.client.chat.completions.create(
            messages=messages,
            model=model,
            **kwargs
        )
        return response

    @staticmethod
    def build_sql_messages(query: str, sql_type: str) -> list[dict]:
        system_instruction = (
            f"Ты — профессиональный SQL-разработчик. Твоя задача — писать запросы на диалекте {sql_type}. "
            "Ответ должен содержать ТОЛЬКО чистый SQL-код. Если запрос невыполним или не связан с SQL, "
            "ответь строго: 'не связано с sql!'. Если запрос потенциально опасен для данных, "
            "в конце ответа добавь маркер: danger."
        )
        
        return [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"Запрос: {query}"}
        ]
    
    @staticmethod
    def is_dangerous(sql_query)->bool:

        if sql_query[-7] == "danger":
            return True
        blacklist = [
            'DROP', 'TRUNCATE', 'GRANT', 'REVOKE', 
            'SHUTDOWN', 'ALTER', 'EXEC', 'VACUUM'
        ]
        

        query = sql_query.upper()
        
 
        pattern = r'\b(' + '|'.join(blacklist) + r')\b'
        if re.search(pattern, query):
            return True
        

        if re.search(r'\b(DELETE|UPDATE)\b', query) and 'WHERE' not in query:
            return True
            
        return False
         

    async def get_query(self, input_text: str, sql_type: str, model: str = "llama-3.3-70b-versatile") -> str:
       
        messages = self.build_sql_messages(input_text, sql_type)
        
       
        resp = await self.get_response(messages=messages, model=model)
        resp = resp.choices[0].message.content.strip()
        if resp == "не связано с sql!":
            raise NotSqlPromt()
        return resp
    

