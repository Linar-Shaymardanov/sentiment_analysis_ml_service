# app/services/crud/transaction.py
from typing import List
from sqlmodel import Session, select
from app.models.transaction import Transaction

def get_transactions_for_user(user_id: int, session: Session) -> List[Transaction]:
    stmt = select(Transaction).where(Transaction.user_id == user_id).order_by(Transaction.timestamp.desc())
    return session.exec(stmt).all()
