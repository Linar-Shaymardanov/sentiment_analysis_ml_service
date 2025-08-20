# app/main.py
from fastapi import FastAPI
import traceback

# подключаем роутеры
from app.routes.auth import router as auth_router
from app.routes.predict import router as predict_router
from app.routes.user import user_route  # если есть

app = FastAPI(title="Sentiment Analysis API", version="1.0.0")

# ===== Подключение роутов =====
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(predict_router, prefix="/api/predict", tags=["predict"])

try:
    app.include_router(user_route, prefix="/api/users", tags=["users"])
except Exception:
    pass

# ===== Служебные эндпоинты =====
@app.get("/")
def root():
    return {"message": "Sentiment Analysis API - root"}

@app.get("/health")
def health():
    return {"status": "ok"}

# ===== Инфо о модели (оставим твой код) =====
try:
    from . import Task_1_v3 as task_module
    MODEL_INFO = {
        "module": getattr(task_module, "__name__", "Task_1_v3"),
        "entities": [name for name in dir(task_module) if name[0].isupper()],
    }
except Exception as e:
    MODEL_INFO = {"error": str(e), "trace": traceback.format_exc()}

@app.get("/model-info")
def model_info():
    return MODEL_INFO

