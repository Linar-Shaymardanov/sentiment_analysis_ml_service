# app/routes/home.py
from typing import Dict
from fastapi import APIRouter

home_route = APIRouter()

@home_route.get("/", summary="Root")
async def root():
    return {"message": "Sentiment Analysis API - root"}

@home_route.get("/health", summary="Health")
async def health():
    return {"status": "ok"}
