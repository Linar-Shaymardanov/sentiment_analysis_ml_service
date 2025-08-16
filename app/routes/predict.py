# app/routes/predict.py
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas import PredictRequest, PredictResponse, PredictionOut
from app.deps import get_current_user
from sqlmodel import Session
from app.database.database import get_session
from app.models.prediction import Prediction as PredictionModel
from app.services.crud.prediction import create_prediction, get_predictions_for_user
from app.services.crud.user import add_credits, charge_credits  # если нужно
from typing import List

router = APIRouter(prefix="/api/predict", tags=["Predict"])

@router.post("/", response_model=PredictResponse)
def predict(payload: PredictRequest, user = Depends(get_current_user), session: Session = Depends(get_session)):
    # Заглушка: "делаем предсказание" — тут должна быть ML-логика
    # Берём фиктивный результат и списываем кредит
    COST = 5
    if user.credits < COST:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Not enough credits")
    # списать — используй сервис charge_credits (он создаёт Transaction)
    tx = charge_credits(user.id, COST, session)
    # фиктивный результат
    result = {"sentiment": "positive", "score": 0.85}
    pred = PredictionModel(user_id=user.id, input_data=payload.text, result=result, cost=COST)
    created = create_prediction(pred, session)
    return {"input": payload.text, "result": result, "cost": COST}

@router.get("/", response_model=List[PredictionOut])
def list_my_predictions(user = Depends(get_current_user), session: Session = Depends(get_session)):
    preds = get_predictions_for_user(user.id, session)
    return preds
