# app/api.py
from fastapi import FastAPI
from app.routes.auth import router as auth_router
from app.routes.predict import router as predict_router
# если есть user_route, импортируй и подключи аналогично

app = FastAPI(title="Sentiment Analysis API", version="1.0.0")

# централизованные префиксы:
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(predict_router, prefix="/api/predict", tags=["predict"])

@app.get("/")
def root():
    return {"message": "Sentiment Analysis API - root"}

@app.get("/health")
def health():
    return {"status": "ok"}
