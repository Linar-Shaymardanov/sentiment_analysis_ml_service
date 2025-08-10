FROM python:3.11-slim

WORKDIR /usr/src/app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PATH="/root/.local/bin:${PATH}"

# system deps (если нужны)
RUN apt-get update && apt-get install -y build-essential gcc libpq-dev --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# копируем код (в dev будем монтировать ./app)
COPY app/ ./app
COPY .env .env

CMD ["python", "-u", "app/main.py"]
