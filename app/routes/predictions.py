# app/routes/predictions.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List
from sqlmodel import Session
from app.database.database import get_session
from app.services.crud.prediction import create_prediction as create_prediction_crud, get_predictions_for_user
from app.models.prediction import Prediction as PredictionModel
from app.schemas import PredictionOut  # если вы сделали schema

router = APIRouter()

class PredictionResultIn(BaseModel):
    user_id: int
    input_data: str
    result: Dict[str, Any]
    cost: int = 0

@router.post("/api/predictions/result")
def accept_prediction(payload: PredictionResultIn, session: Session = Depends(get_session)):
    try:
        pred = PredictionModel(
            user_id=payload.user_id,
            input_data=payload.input_data,
            result=payload.result,
            cost=payload.cost
        )
        created = create_prediction_crud(pred, session)
        return {"message": "saved", "prediction_id": created.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/predictions/user/{user_id}", response_model=List[PredictionOut])
def list_user_predictions(user_id: int, session: Session = Depends(get_session)):
    preds = get_predictions_for_user(user_id, session)
    return preds
