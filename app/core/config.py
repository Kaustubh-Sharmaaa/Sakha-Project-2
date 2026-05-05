from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "Sakha Project 2"
    secret_key: str = "your-super-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    surrealdb_url: str = "mem://"  # in-memory for dev; use ws:// for persistent

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
