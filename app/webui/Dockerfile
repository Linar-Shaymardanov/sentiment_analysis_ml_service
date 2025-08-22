FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# requirements.txt is in the same folder as this Dockerfile (context = ./app/webui)
COPY requirements.txt /tmp/req.txt

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && pip install --upgrade pip setuptools wheel \
 && pip install --no-cache-dir -r /tmp/req.txt \
 && rm -rf /var/lib/apt/lists/*

# copy all webui files from context (./app/webui) into /app
COPY . /app

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]

