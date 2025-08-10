# app/services/crud/user.py
from sqlmodel import Session, select
from app.models.user import User
from app.models.transaction import Transaction
from app.models.prediction import Prediction
from typing import Optional, List

def create_user(user: User, session: Session) -> User:
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

def get_user_by_email(email: str, session: Session) -> Optional[User]:
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()

def get_user_by_id(user_id: int, session: Session) -> Optional[User]:
    return session.get(User, user_id)

def top_up_user(user_id: int, amount: int, session: Session, description: str = "Top up") -> Transaction:
    user = session.get(User, user_id)
    if not user:
        raise ValueError("User not found")
    user.credits += amount
    tx = Transaction(user_id=user.id, amount=amount, description=description)
    session.add(user)
    session.add(tx)
    session.commit()
    session.refresh(tx)
    return tx

def charge_user(user_id: int, amount: int, session: Session, description: str = "Charge") -> Transaction:
    user = session.get(User, user_id)
    if not user:
        raise ValueError("User not found")
    if user.credits < amount:
        raise ValueError("Insufficient credits")
    user.credits -= amount
    tx = Transaction(user_id=user.id, amount=-amount, description=description)
    session.add(user)
    session.add(tx)
    session.commit()
    session.refresh(tx)
    return tx

def get_transactions_for_user(user_id: int, session: Session) -> List[Transaction]:
    statement = select(Transaction).where(Transaction.user_id == user_id).order_by(Transaction.timestamp.desc())
    return session.exec(statement).all()

def create_prediction(user_id: int, input_data: str, result: dict, cost: int, session: Session) -> Prediction:
    pred = Prediction(user_id=user_id, input_data=input_data, result=result, cost=cost)
    session.add(pred)
    session.commit()
    session.refresh(pred)
    return pred

def get_predictions_for_user(user_id: int, session: Session):
    statement = select(Prediction).where(Prediction.user_id == user_id).order_by(Prediction.timestamp.desc())
    return session.exec(statement).all()
