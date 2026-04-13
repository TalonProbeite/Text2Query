# app/dependencies.py
from functools import lru_cache
from app.services.llm_service import LlmService
from app.core.config import settings

@lru_cache
def get_llm_service() -> LlmService:
    return LlmService(api_key=settings.llm.api_key, base_url=settings.llm.base_url)