# app/database/database.py
from sqlmodel import SQLModel, Session, create_engine
from contextlib import contextmanager
from .config import get_settings

def get_database_engine():
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL_psycopg, echo=settings.DEBUG)
    return engine

# engine для общего использования
engine = get_database_engine()

def init_db(drop_all: bool = False):
    if drop_all:
        SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)

# FastAPI dependency
def get_session():
    with Session(engine) as session:
        yield session
