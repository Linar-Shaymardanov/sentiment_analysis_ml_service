# app/services/crud/prediction.py
from typing import List
from sqlmodel import Session, select
from app.models.prediction import Prediction

def create_prediction(pred: Prediction, session: Session) -> Prediction:
    session.add(pred)
    session.commit()
    session.refresh(pred)
    return pred

def get_predictions_for_user(user_id: int, session: Session) -> List[Prediction]:
    stmt = select(Prediction).where(Prediction.user_id == user_id).order_by(Prediction.timestamp.desc())
    return session.exec(stmt).all()

