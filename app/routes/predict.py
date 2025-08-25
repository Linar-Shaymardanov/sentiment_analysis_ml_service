# app/routes/predict.py
from fastapi import APIRouter, HTTPException
from typing import List, Any, Dict
import json
import os
import pika

from sqlmodel import Session, select
from app.database.database import engine
from app.models.prediction import Prediction
from app.schemas import PredictionOut, PredictRequest

router = APIRouter()

def _normalize_result_field(val: Any) -> Dict:
    if isinstance(val, str):
        try:
            return json.loads(val)
        except Exception:
            return {}
    if val is None:
        return {}
    # if already a dict or json-like, return as-is
    return val

@router.get("/", response_model=List[PredictionOut])
def list_predictions():
    with Session(engine) as session:
        rows = session.exec(select(Prediction).order_by(Prediction.id.desc())).all()
        # гарантируем, что поле result — dict, а не строка
        for r in rows:
            r.result = _normalize_result_field(r.result)
        return rows

@router.post("/queue", status_code=202)
def enqueue_predict(req: PredictRequest):
    payload = {"text": req.text}
    host = os.getenv("RABBITMQ_HOST", "rabbitmq")
    user = os.getenv("RABBITMQ_USER", "rmuser")
    pwd = os.getenv("RABBITMQ_PASS", "rmpassword")
    queue = os.getenv("PREDICTION_QUEUE", "predictions")

    creds = pika.PlainCredentials(user, pwd)
    params = pika.ConnectionParameters(host=host, credentials=creds)
    try:
        conn = pika.BlockingConnection(params)
        ch = conn.channel()
        ch.queue_declare(queue=queue, durable=True)
        ch.basic_publish(
            exchange="",
            routing_key=queue,
            body=json.dumps(payload).encode("utf-8"),
            properties=pika.BasicProperties(delivery_mode=2),
        )
        conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to enqueue: {e}")
    return {"status": "queued"}

@router.post("/result")
def receive_result(payload: Dict):
    # minimal validation
    for field in ("user_id", "input_data", "result"):
        if field not in payload:
            raise HTTPException(status_code=400, detail=f"Missing field: {field}")

    payload["result"] = _normalize_result_field(payload.get("result"))
    from sqlmodel import Session as _Session
    with _Session(engine) as session:
        p = Prediction(
            user_id=payload["user_id"],
            model_name=payload.get("model_name"),
            input_data=payload.get("input_data"),
            result=payload["result"],
            cost=payload.get("cost", 0),
        )
        session.add(p)
        session.commit()
        session.refresh(p)
    return {"status": "ok", "id": p.id}
