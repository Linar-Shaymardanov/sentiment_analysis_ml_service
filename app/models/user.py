# app/models/user.py
from typing import List, Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .transaction import Transaction
    from .prediction import Prediction

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, nullable=False, unique=True)
    password: str  # в учебном задании можно хранить в явном виде
    is_admin: bool = Field(default=False)
    credits: int = Field(default=0)

    transactions: List["Transaction"] = Relationship(back_populates="user")
    predictions: List["Prediction"] = Relationship(back_populates="user")
