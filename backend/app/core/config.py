import os
import secrets
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Base settings
    PROJECT_NAME: str = "StepIn"
    PROJECT_DESCRIPTION: str = "Physical Meeting Management Platform"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = secrets.token_urlsafe(32)

    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8

    # CORS settings
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database settings
    USE_POSTGRES: bool = True
    DB_PATH: str = "stepin.db"  # For SQLite
    DB_HOST: str = "localhost"  # For PostgreSQL
    DB_NAME: str = "stepin"     # For PostgreSQL
    DB_USER: str = "postgres"   # For PostgreSQL
    DB_PASSWORD: str = "postgres"  # For PostgreSQL

    # Redis settings
    USE_FAKE_REDIS: bool = False
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # Application settings
    PORT: int = 8000

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()