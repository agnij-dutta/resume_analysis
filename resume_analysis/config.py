from pydantic_settings import BaseSettings
import os

class Config(BaseSettings):
    HUGGINGFACE_TOKEN: str
    GITHUB_TOKEN: str | None = None
    MAX_REQUESTS_PER_MINUTE: int = 60
    CACHE_TTL: int = 3600
    
    class Config:
        env_file = ".env"
        case_sensitive = True