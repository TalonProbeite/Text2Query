from  pydantic_settings import BaseSettings , SettingsConfigDict 
from typing import List
from pathlib import Path 
import base64
from pydantic import BaseModel

BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent

class JWTSettings(BaseModel):
    private_key_b64: str
    public_key_b64: str
    algorithm: str = "RS256"

    @property
    def private_key(self) -> str:
        return base64.b64decode(self.private_key_b64).decode("utf-8")

    @property
    def public_key(self) -> str:
        return base64.b64decode(self.public_key_b64).decode("utf-8")

class RedisSettings(BaseModel):
    url:str

class DatabaseSettings(BaseModel):
    url: str


class LLMSettings(BaseModel):
    api_key: str
    base_url: str = "https://api.groq.com/openai/v1"
    model: str = "llama-3.3-70b-versatile"


class Settings(BaseSettings):
    app_name: str = "SQLCraft"
    debug: bool = False
    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]
    static_dir: Path =  BASE_DIR / "frontend"

    db: DatabaseSettings
    jwt: JWTSettings
    llm: LLMSettings
    redis:RedisSettings

    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__")


settings = Settings()