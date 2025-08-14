# app/main.py
from fastapi import FastAPI
import importlib
import traceback

app = FastAPI(title="Sentiment ML Service (placeholder)")

# Попробуем импортировать модуль Task_1_v3 внутри пакета app
try:
    # relative import; пакет app должен быть в PYTHONPATH (WORKDIR = /usr/src/app)
    from . import Task_1_v3 as task_module
    MODEL_INFO = {
        "module": getattr(task_module, "__name__", "Task_1_v3"),
        "entities": [name for name in dir(task_module) if name[0].isupper()],
    }
except Exception as e:
    MODEL_INFO = {"error": str(e), "trace": traceback.format_exc()}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/model-info")
def model_info():
    return MODEL_INFO

# simple root
@app.get("/")
def root():
    return {"msg": "Sentiment Analysis ML Service (placeholder)", "health": health()}
