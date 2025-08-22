# app/models/transaction.py
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .user import User

class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    amount: int  # + пополнение, - списание
    description: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    user: "User" = Relationship(back_populates="transactions")
