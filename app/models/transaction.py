# app/models/transaction.py
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", nullable=False, index=True)
    amount: int
    description: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    user: "User" = Relationship(back_populates="transactions")
