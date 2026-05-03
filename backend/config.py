import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: Optional[str] = None
    jwt_secret: str = "change-me-in-production"
    database_url: str = "sqlite:///./data/dorm.db"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
