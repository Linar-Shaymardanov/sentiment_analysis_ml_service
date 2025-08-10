# app/models/prediction.py
from typing import Optional, Dict, Any
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import JSON

class Prediction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", nullable=False, index=True)
    input_data: Optional[str] = None
    result: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    cost: int = Field(default=0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    user: "User" = Relationship(back_populates="predictions")
