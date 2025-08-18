# app/schemas.py
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from datetime import datetime

# ---------- Auth ----------
class UserCreate(BaseModel):
    email: str
    password: str

class UserSignIn(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[int] = None

# ---------- User output ----------
class UserOut(BaseModel):
    id: int
    email: str        # <-- changed from EmailStr to str
    is_admin: bool
    credits: int

    # Pydantic v2: allow creating model from ORM objects
    model_config = {"from_attributes": True}

# ---------- Transactions / Predictions ----------
class TopUpRequest(BaseModel):
    amount: int

class TransactionOut(BaseModel):
    id: int
    user_id: int
    amount: int
    description: Optional[str]
    timestamp: datetime

    model_config = {"from_attributes": True}

class PredictRequest(BaseModel):
    text: str

class PredictResponse(BaseModel):
    input: str
    result: Dict[str, Any]
    cost: int

class PredictionOut(BaseModel):
    id: int
    user_id: int
    input_data: str
    result: Dict[str, Any]
    cost: int
    timestamp: datetime

    model_config = {"from_attributes": True}
