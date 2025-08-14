# app/database/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    DB_HOST: Optional[str] = "database"
    DB_PORT: Optional[int] = 5432
    DB_USER: Optional[str] = "postgres"
    DB_PASS: Optional[str] = "postgres"
    DB_NAME: Optional[str] = "app_db"

    APP_NAME: Optional[str] = "Sentiment API"
    DEBUG: Optional[bool] = False
    API_VERSION: Optional[str] = "0.1.0"

    @property
    def DATABASE_URL_psycopg(self):
        return f"postgresql+psycopg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True)

    def validate(self):
        if not all([self.DB_HOST, self.DB_USER, self.DB_PASS, self.DB_NAME]):
            raise ValueError("Missing DB config")

@lru_cache()
def get_settings() -> Settings:
    s = Settings()
    s.validate()
    return s
