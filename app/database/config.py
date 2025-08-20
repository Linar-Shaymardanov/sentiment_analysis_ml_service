# app/database/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # Database settings
    DB_HOST: Optional[str] = None
    DB_PORT: Optional[int] = 5432
    DB_USER: Optional[str] = None
    DB_PASS: Optional[str] = None
    DB_NAME: Optional[str] = None

    # Application settings
    APP_NAME: Optional[str] = "Sentiment ML Service"
    APP_DESCRIPTION: Optional[str] = None
    DEBUG: Optional[bool] = False
    API_VERSION: Optional[str] = "1.0"

    # RabbitMQ / worker settings
    RABBITMQ_HOST: Optional[str] = "rabbitmq"
    RABBITMQ_USER: Optional[str] = "rmuser"
    RABBITMQ_PASS: Optional[str] = "rmpassword"
    PREDICTION_QUEUE: Optional[str] = "predictions"
    API_CALLBACK: Optional[str] = "http://app:8080/api/predictions/result"

    @property
    def DATABASE_URL_asyncpg(self) -> str:
        return f'postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'

    @property
    def DATABASE_URL_psycopg(self) -> str:
        # SQLAlchemy psycopg driver
        return f'postgresql+psycopg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

    def validate(self) -> None:
        """Validate critical configuration settings"""
        if not all([self.DB_HOST, self.DB_USER, self.DB_PASS, self.DB_NAME]):
            raise ValueError("Missing required database configuration")

@lru_cache()
def get_settings() -> Settings:
    s = Settings()
    # не вызывать s.validate(), т.к. при локальной отладке можно пропустить db (но если нужно — включите)
    return s
