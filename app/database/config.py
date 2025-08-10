# app/database/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    DB_HOST: Optional[str] = "database"
    DB_PORT: Optional[int] = 5432
    DB_USER: Optional[str] = "postgres"
    DB_PASS: Optional[str] = "password"
    DB_NAME: Optional[str] = "app_db"

    APP_NAME: Optional[str] = "sentiment-service"
    DEBUG: Optional[bool] = True
    API_VERSION: Optional[str] = "v1"

    @property
    def DATABASE_URL_psycopg(self) -> str:
        return f'postgresql+psycopg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

    def validate(self) -> None:
        if not all([self.DB_HOST, self.DB_USER, self.DB_PASS, self.DB_NAME]):
            raise ValueError("Missing required database configuration")

@lru_cache()
def get_settings() -> Settings:
    s = Settings()
    s.validate()
    return s
