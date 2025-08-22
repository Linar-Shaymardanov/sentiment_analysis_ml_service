# app/services/crud/user.py
from typing import Optional, List
from sqlmodel import Session, select
from app.models.user import User
from app.models.transaction import Transaction

def get_user_by_id(user_id: int, session: Session) -> Optional[User]:
    return session.get(User, user_id)

def get_user_by_email(email: str, session: Session) -> Optional[User]:
    stmt = select(User).where(User.email == email)
    return session.exec(stmt).first()

def create_user(user: User, session: Session) -> User:
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

def list_users(session: Session) -> List[User]:
    stmt = select(User)
    return session.exec(stmt).all()

def add_credits(user_id: int, amount: int, session: Session) -> Transaction:
    if amount <= 0:
        raise ValueError("Amount must be > 0")
    user = get_user_by_id(user_id, session)
    if not user:
        raise ValueError("User not found")
    user.credits += amount
    tx = Transaction(user_id=user_id, amount=amount, description="top-up")
    session.add(tx)
    session.add(user)
    session.commit()
    session.refresh(tx)
    return tx

def charge_credits(user_id: int, amount: int, session: Session) -> Transaction:
    if amount <= 0:
        raise ValueError("Amount must be > 0")
    user = get_user_by_id(user_id, session)
    if not user:
        raise ValueError("User not found")
    if user.credits < amount:
        raise ValueError("Insufficient balance")
    user.credits -= amount
    tx = Transaction(user_id=user_id, amount=-amount, description="charge")
    session.add(tx)
    session.add(user)
    session.commit()
    session.refresh(tx)
    return tx
