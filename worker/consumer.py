# worker/consumer.py
import os
import json
import time
import logging
import requests
import pika
from typing import Any, Dict

# импорт вашей функции предсказания
from app.Task_1_v3 import run_prediction, ValidationError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("worker")

RABBIT_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBIT_USER = os.getenv("RABBITMQ_USER", "rmuser")
RABBIT_PASS = os.getenv("RABBITMQ_PASS", "rmpassword")
QUEUE_NAME = os.getenv("PREDICTION_QUEUE", "predictions")
API_CALLBACK = os.getenv("API_CALLBACK", "http://app:8080/api/predict/result")
RETRY_DELAY = int(os.getenv("WORKER_RETRY_DELAY", "3"))
PREFETCH_COUNT = int(os.getenv("PREFETCH_COUNT", "1"))

def post_result_to_api(result: Dict[str, Any]) -> None:
    """
    Преобразуем result из run_prediction в структуру, ожидаемую API,
    и POST'им её в callback endpoint приложения.
    """
    # Преобразование полей в формат app (model_name, input_meta, result_json, cost, ...)
    payload = {
        "user_id": result.get("user_id"),
        "model_name": result.get("model") or "text-rule-v1",
        "input_meta": result.get("input_data"),
        "result_json": json.dumps(result.get("result")) if result.get("result") is not None else None,
        "cost": result.get("cost", 1),
        "errors": result.get("errors", []),
        "timestamp": result.get("timestamp"),
    }

    headers = {"Content-Type": "application/json"}
    try:
        resp = requests.post(API_CALLBACK, json=payload, headers=headers, timeout=10)
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to POST to API callback: {e}") from e

    if not (200 <= resp.status_code < 300):
        # пробрасываем ошибку с подробностями ответа API
        raise RuntimeError(f"Callback returned status {resp.status_code}: {resp.text}")

def process_message(body: bytes) -> Dict[str, Any]:
    """Parse JSON, run prediction and return the dict that will be posted."""
    try:
        payload = json.loads(body.decode("utf-8"))
    except Exception as e:
        raise ValidationError(f"Invalid JSON payload: {e}")

    # run prediction (validates internally)
    out = run_prediction(payload)
    return out

def main():
    creds = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
    params = pika.ConnectionParameters(host=RABBIT_HOST, credentials=creds, heartbeat=60)

    # try to connect with retries
    while True:
        try:
            log.info(f"Trying to connect to RabbitMQ at {RABBIT_HOST} ...")
            conn = pika.BlockingConnection(params)
            break
        except Exception as e:
            log.warning("RabbitMQ not ready yet: %s. Retrying in %s s...", e, RETRY_DELAY)
            time.sleep(RETRY_DELAY)

    ch = conn.channel()
    ch.queue_declare(queue=QUEUE_NAME, durable=True)
    ch.basic_qos(prefetch_count=PREFETCH_COUNT)

    log.info("Connected to RabbitMQ")
    log.info("Worker started consuming")

    def callback(ch, method, properties, body):
        delivery_tag = method.delivery_tag
        try:
            log.info("Received message (delivery_tag=%s)", delivery_tag)
            result = process_message(body)
            # POST to app callback (mapped payload inside function)
            post_result_to_api(result)
            ch.basic_ack(delivery_tag=delivery_tag)
            log.info("Processed and acknowledged message (delivery_tag=%s)", delivery_tag)
        except ValidationError as ve:
            log.error("Validation error for message %s: %s. Discarding message.", delivery_tag, ve)
            ch.basic_ack(delivery_tag=delivery_tag)  # bad payload -> discard
        except Exception as e:
            log.exception("Failed to process message (delivery_tag=%s): %s", delivery_tag, e)
            # don't ack -> message will be requeued / retried
            time.sleep(1)

    ch.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=False)

    try:
        ch.start_consuming()
    except KeyboardInterrupt:
        log.info("Interrupt received, stopping...")
    finally:
        if conn and not conn.is_closed:
            conn.close()
        log.info("Worker stopped.")

if __name__ == "__main__":
    main()
