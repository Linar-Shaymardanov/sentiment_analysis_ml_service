# app/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.schemas import UserCreate, UserSignIn, Token, UserOut
from app.database.database import get_session
from app.services.crud.user import create_user, get_user_by_email
from app.utils.jwt import create_access_token

# убираем prefix — префикс будет в api.py
router = APIRouter(tags=["Auth"])

@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def signup(data: UserCreate, session: Session = Depends(get_session)):
    # Простая регистрация (без хеширования — как разрешено)
    if get_user_by_email(data.email, session):
        raise HTTPException(status_code=409, detail="User already exists")

    from app.models.user import User as UserModel
    user_model = UserModel(email=data.email, password=data.password, credits=0, is_admin=False)
    created = create_user(user_model, session)
    return created

@router.post("/signin", response_model=Token)
def signin(data: UserSignIn, session: Session = Depends(get_session)):
    user = get_user_by_email(data.email, session)
    if not user or user.password != data.password:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Wrong credentials")
    token = create_access_token({"user_id": user.id})
    return {"access_token": token, "token_type": "bearer"}
