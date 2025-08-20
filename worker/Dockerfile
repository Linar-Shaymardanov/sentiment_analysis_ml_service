FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/usr/src/app

WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential gcc libpq-dev curl && rm -rf /var/lib/apt/lists/*

COPY worker/requirements.txt /tmp/worker-reqs.txt

RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r /tmp/worker-reqs.txt

COPY app /usr/src/app/app
COPY worker /usr/src/app/worker

CMD ["python", "-u", "worker/consumer.py"]



