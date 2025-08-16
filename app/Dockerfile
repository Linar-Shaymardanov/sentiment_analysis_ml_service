# ./app/Dockerfile
FROM python:3.11-slim

# Не слишком много слоёв, всё минимально
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
# Добавляем родительский путь, чтобы импорты 'app.*' работали
ENV PYTHONPATH=/usr/src

WORKDIR /usr/src/app

# системные зависимости для сборки (psycopg и т.п.)
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Копируем только requirements и ставим зависимости
COPY requirements.txt /usr/src/app/requirements.txt
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r /usr/src/app/requirements.txt

# Копируем весь код приложения
COPY . /usr/src/app

EXPOSE 8080

# Убедимся, что uvicorn импортирует модуль api.py (который в /usr/src/app)
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8080", "--log-level", "info"]

