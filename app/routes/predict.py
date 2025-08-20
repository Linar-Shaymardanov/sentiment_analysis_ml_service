# app/routes/predict.py
import os
import json
import pika
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlmodel import Session
from app.schemas import PredictRequest, PredictResponse, PredictionOut
from app.deps import get_current_user
from app.database.database import get_session
from app.models.prediction import Prediction as PredictionModel
from app.services.crud.prediction import create_prediction, get_predictions_for_user
from app.services.crud.user import charge_credits

# убираем prefix — зададим его в api.py
router = APIRouter(tags=["Predict"])

RABBIT_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBIT_USER = os.getenv("RABBITMQ_USER", "rmuser")
RABBIT_PASS = os.getenv("RABBITMQ_PASS", "rmpassword")
QUEUE_NAME = os.getenv("PREDICTION_QUEUE", "predictions")

def publish_to_queue(payload: dict):
    creds = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
    params = pika.ConnectionParameters(host=RABBIT_HOST, credentials=creds, heartbeat=60)
    conn = pika.BlockingConnection(params)
    ch = conn.channel()
    ch.queue_declare(queue=QUEUE_NAME, durable=True)
    body = json.dumps(payload)
    ch.basic_publish(
        exchange="",
        routing_key=QUEUE_NAME,
        body=body,
        properties=pika.BasicProperties(delivery_mode=2)
    )
    conn.close()

@router.post("/queue", status_code=status.HTTP_202_ACCEPTED)
def enqueue_predict(payload: PredictRequest, user = Depends(get_current_user), session: Session = Depends(get_session)):
    COST = 1
    try:
        tx = charge_credits(user.id, COST, session)
    except Exception as e:
        raise HTTPException(status_code=402, detail=str(e))

    msg = {"user_id": user.id, "input_data": payload.text}
    try:
        publish_to_queue(msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to publish task: {e}")

    return {"message": "Task queued", "cost": COST}

@router.post("/result", status_code=200)
def prediction_result(data: dict = Body(...), session: Session = Depends(get_session)):
    required = ("user_id", "input_data", "result", "cost")
    for k in required:
        if k not in data:
            raise HTTPException(status_code=400, detail=f"Missing {k} in body")

    pred = PredictionModel(
        user_id=int(data["user_id"]),
        input_data=data["input_data"],
        result=data["result"],
        cost=int(data["cost"])
    )
    try:
        created = create_prediction(pred, session)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create prediction: {e}")
    return {"message": "Prediction recorded", "id": created.id}

@router.get("/", response_model=List[PredictionOut])
def list_my_predictions(user = Depends(get_current_user), session: Session = Depends(get_session)):
    preds = get_predictions_for_user(user.id, session)
    return preds
