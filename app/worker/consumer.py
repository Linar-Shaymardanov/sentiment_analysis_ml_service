# app/worker/consumer.py
import pika
import os
import json
import time
import requests

RABBIT_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBIT_USER = os.getenv("RABBITMQ_USER", "rmuser")
RABBIT_PASS = os.getenv("RABBITMQ_PASS", "rmpassword")
QUEUE_NAME = os.getenv("PREDICTION_QUEUE", "predictions")
API_CALLBACK = os.getenv("API_CALLBACK", "http://app:8080/api/predictions/result")

def predict_stub(text: str):
    # простая заглушка предсказания
    text = text.lower()
    if "love" in text or "good" in text:
        return {"sentiment": "positive", "score": 0.9}
    if "bad" in text or "hate" in text:
        return {"sentiment": "negative", "score": 0.1}
    return {"sentiment": "neutral", "score": 0.5}

def callback(ch, method, properties, body):
    try:
        payload = json.loads(body.decode("utf-8"))
        print("Worker received:", payload)
        if "user_id" not in payload or "input_data" not in payload:
            print("Invalid payload, acking and dropping:", payload)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        user_id = int(payload["user_id"])
        input_text = payload["input_data"]
        time.sleep(1)  # simulate work
        result = predict_stub(input_text)

        post_payload = {
            "user_id": user_id,
            "input_data": input_text,
            "result": result,
            "cost": 1
        }
        try:
            resp = requests.post(API_CALLBACK, json=post_payload, timeout=10)
            print("Callback POST status:", resp.status_code)
            if resp.status_code == 200:
                ch.basic_ack(delivery_tag=method.delivery_tag)
            else:
                print("Callback failed, requeueing")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        except Exception as e:
            print("Error calling API callback:", e)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    except Exception as e:
        print("Unexpected worker error:", e)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

def run():
    creds = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
    params = pika.ConnectionParameters(host=RABBIT_HOST, credentials=creds, heartbeat=60)
    # Пытаемся подключиться в цикле (retry) — важно, т.к. rabbitmq может стартовать дольше
    retry_delay = 3
    while True:
        try:
            print(f"Trying to connect to RabbitMQ at {RABBIT_HOST} ...")
            conn = pika.BlockingConnection(params)
            print("Connected to RabbitMQ")
            break
        except Exception as e:
            print(f"RabbitMQ not ready yet: {e}. Retrying in {retry_delay}s...")
            time.sleep(retry_delay)
            # optional: увеличить retry_delay или добавить лимит попыток

    ch = conn.channel()
    ch.queue_declare(queue=QUEUE_NAME, durable=True)
    ch.basic_qos(prefetch_count=1)
    ch.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)
    print("Worker started consuming")
    ch.start_consuming()

if __name__ == "__main__":
    run()
