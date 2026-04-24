from  pydantic_settings import BaseSettings , SettingsConfigDict 
from typing import List
from pathlib import Path 
import base64
from pydantic import BaseModel
from fastapi_mail  import ConnectionConfig


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
    DATABASE_HOST:str
    DATABASE_USER:str
    DATABASE_PASSWORD:str
    DATABASE_NAME:str

    @property
    def url(self)->str:
        return f"postgresql+asyncpg://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}/{self.DATABASE_NAME}?ssl=require"

class MailSettings(BaseModel):
    MAIL_USERNAME:str
    MAIL_PASSWORD:str
    MAIL_FROM:str
    MAIL_PORT:int = 587
    MAIL_FROM_NAME:str="SqlCraft Support"
    MAIL_SERVER:str = "smtp.gmail.com"
    MAIL_STARTTLS:bool = True
    MAIL_SSL_TLS:bool = False
    USE_CREDENTIALS:bool = True
    VALIDATE_CERTS:bool = True

    @property
    def config(self) -> ConnectionConfig:
        return  ConnectionConfig(
            MAIL_USERNAME=self.MAIL_USERNAME,
            MAIL_PASSWORD=self.MAIL_PASSWORD, 
            MAIL_FROM=self.MAIL_FROM,
            MAIL_FROM_NAME=self.MAIL_FROM_NAME,
            MAIL_PORT=self.MAIL_PORT,
            MAIL_SERVER=self.MAIL_SERVER,
            MAIL_STARTTLS=self.MAIL_STARTTLS,
            MAIL_SSL_TLS=self.MAIL_SSL_TLS,
            USE_CREDENTIALS=self.USE_CREDENTIALS,
            VALIDATE_CERTS=self.VALIDATE_CERTS)

class LLMSettings(BaseModel):
    api_key: str
    base_url: str = "https://api.groq.com/openai/v1"
    model: str = "llama-3.3-70b-versatile"

class CryptoSettings(BaseModel):
    key:str

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
    mail:MailSettings
    crypto: CryptoSettings

    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__")


settings = Settings()