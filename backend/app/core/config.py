from  pydantic_settings import BaseSettings , SettingsConfigDict
from typing import List
from pathlib import Path 
import base64

BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseSettings):

    app_name: str = "SQLCraft"
    debug: bool = False

    database_url: str = "postgresql://user:pass@localhost/sqlcraft"

    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    
    static_dir: Path =  BASE_DIR / "frontend"
    
    # private_key : str = (BASE_DIR / "certs" / "private.pem").read_text().strip()
    # public_key : str = (BASE_DIR / "certs" / "public.pem").read_text().strip()
    private_key_b64: str
    public_key_b64: str
    @property
    def private_key(self) -> str:
        return base64.b64decode(self.private_key_b64).decode("utf-8")

    @property
    def public_key(self) -> str:
        return base64.b64decode(self.public_key_b64).decode("utf-8")
    
    algorithm: str = "RS256"

    llm_api_key:str

    model_config = SettingsConfigDict(
    env_file=BASE_DIR / ".env",
    extra="ignore"
)

settings = Settings()