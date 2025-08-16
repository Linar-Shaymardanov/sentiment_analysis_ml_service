# app/api.py  (обновлён)
from fastapi import FastAPI
from app.routes import home  # если есть
from app.routes.auth import router as auth_router
from app.routes.predict import router as predict_router
from app.routes.user import user_route  # если есть старый роутер пользователя

app = FastAPI(title="Sentiment Analysis API", version="1.0.0")

app.include_router(auth_router)
app.include_router(predict_router)
# если есть user routes отдельно:
try:
    app.include_router(user_route)
except Exception:
    pass

@app.get("/")
def root():
    return {"message": "ok"}

@app.get("/health")
def health():
    return {"status": "ok"}
