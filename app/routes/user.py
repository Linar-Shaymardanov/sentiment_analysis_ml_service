# app/routes/user.py
from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.database.database import get_session
from app.models.user import User
from app.services.crud import user as UserService, transaction as TxService

user_route = APIRouter()

@user_route.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(data: User, session: Session = Depends(get_session)) -> Dict[str, str]:
    if UserService.get_user_by_email(data.email, session):
        raise HTTPException(status_code=409, detail="User exists")
    user = User(email=data.email, password=data.password)
    UserService.create_user(user, session)
    return {"message": "registered", "user_id": user.id}

@user_route.post("/signin")
def signin(data: User, session: Session = Depends(get_session)):
    user = UserService.get_user_by_email(data.email, session)
    if not user or user.password != data.password:
        raise HTTPException(status_code=403, detail="Wrong credentials")
    return {"message": "signed in", "user_id": user.id}

@user_route.post("/{user_id}/topup")
def topup(user_id: int, amount: int, session: Session = Depends(get_session)):
    try:
        tx = UserService.add_credits(user_id, amount, session)
        return {"message": "topped up", "transaction_id": tx.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@user_route.post("/{user_id}/charge")
def charge(user_id: int, amount: int, session: Session = Depends(get_session)):
    try:
        tx = UserService.charge_credits(user_id, amount, session)
        return {"message": "charged", "transaction_id": tx.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@user_route.get("/{user_id}/transactions")
def transactions(user_id: int, session: Session = Depends(get_session)):
    return TxService.get_transactions_for_user(user_id, session)
