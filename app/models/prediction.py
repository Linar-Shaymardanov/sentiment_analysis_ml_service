# app/models/prediction.py
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .user import User

class Prediction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    model_name: str
    input_meta: Optional[str] = None
    result_json: Optional[str] = Field(default=None, nullable=True)  # сохраняем JSON как строку
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    user: "User" = Relationship(back_populates="predictions")
