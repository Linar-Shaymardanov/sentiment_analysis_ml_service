# app/models/prediction.py
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB

if TYPE_CHECKING:
    from .user import User

class Prediction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", nullable=False)
    model_name: Optional[str] = Field(default="text-rule-v1")
    input_data: Optional[str] = Field(default=None, nullable=True)
    # хранить результат как JSON (Postgres JSONB)
    result: Optional[dict] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    cost: int = Field(default=0)

    user: "User" = Relationship(back_populates="predictions")

