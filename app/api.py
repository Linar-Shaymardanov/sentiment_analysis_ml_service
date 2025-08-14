from fastapi import FastAPI

app = FastAPI(
    title="Sentiment Analysis API",
    description="API для анализа тональности текста",
    version="1.0.0"
)

@app.get("/")
def root():
    return {"message": "Сервис запущен успешно"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
