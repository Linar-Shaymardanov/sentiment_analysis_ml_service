# webui/streamlit_app.py
"""
Streamlit web UI для ML-сервиса (интеграция с FastAPI backend).
"""

import os
import streamlit as st
import requests
import json
import base64
import csv
from io import StringIO
from typing import Optional, List, Dict, Tuple

# ============================
# Настройки: ENV > secrets > default
# ============================
API_BASE = os.environ.get("API_BASE")
if not API_BASE:
    try:
        API_BASE = st.secrets.get("API_BASE", None)
    except Exception:
        API_BASE = None
API_BASE = API_BASE or "http://localhost:8080"

SIGNUP_URL = f"{API_BASE}/api/auth/signup"
SIGNIN_URL = f"{API_BASE}/api/auth/signin"
PREDICT_QUEUE_URL = f"{API_BASE}/api/predict/queue"
PREDICT_LIST_URL = f"{API_BASE}/api/predict/"
TOPUP_URL = f"{API_BASE}/api/user/topup"   # опционально
# PROFILE_URL = f"{API_BASE}/api/user/me"  # backend не реализует
PREDICTION_RESULT_CALLBACK = f"{API_BASE}/api/predict/result"  # опционально

# ============================
# ---- helper-утилиты ----
# ============================
def api_post(url: str, json_data: dict = None, data: dict = None, headers: dict = None, timeout=10):
    try:
        if data is not None:
            resp = requests.post(url, data=data, headers=headers, timeout=timeout)
        else:
            resp = requests.post(url, json=json_data, headers=headers, timeout=timeout)
        return resp
    except Exception as e:
        st.error(f"Network error: {e}")
        return None

def api_get(url: str, headers: dict = None, params: dict = None, timeout=10):
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=timeout)
        return resp
    except Exception as e:
        st.error(f"Network error: {e}")
        return None

def set_token(token: str):
    st.session_state["token"] = token
    st.session_state["auth_headers"] = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

def clear_token():
    st.session_state.pop("token", None)
    st.session_state.pop("auth_headers", None)
    st.session_state.pop("profile", None)

def decode_jwt_payload(token: str) -> dict:
    """Декодируем payload JWT без проверки подписи (для UI)."""
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return {}
        payload_b64 = parts[1] + "=" * ((4 - len(parts[1]) % 4) % 4)
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        return json.loads(payload_bytes)
    except Exception:
        return {}

# ============================
# ---- API функции ----
# ============================
def signup(email: str, password: str) -> Tuple[bool, str]:
    payload = {"email": email, "password": password}
    resp = api_post(SIGNUP_URL, json_data=payload)
    if resp is None:
        return False, "Network error"
    if resp.status_code in (200, 201):
        return True, "User created"
    try:
        return False, resp.json().get("detail", resp.text)
    except Exception:
        return False, resp.text

def signin(email: str, password: str) -> Tuple[bool, Optional[str]]:
    payload = {"email": email, "password": password}
    resp = api_post(SIGNIN_URL, json_data=payload,
                    headers={"Content-Type": "application/json"})
    if resp is None:
        return False, None
    if resp.status_code in (200, 201):
        try:
            j = resp.json()
            token = j.get("access_token") or j.get("token") or j.get("access")
            if not token and isinstance(j, dict):
                for v in j.values():
                    if isinstance(v, str) and v.count(".") == 2:
                        token = v
                        break
            return True, token
        except Exception:
            st.error("Unexpected signin response: " + resp.text)
            return False, None
    else:
        try:
            return False, resp.json().get("detail", resp.text)
        except Exception:
            return False, resp.text

def topup(amount: int) -> Tuple[bool, str]:
    headers = st.session_state.get("auth_headers")
    if not headers:
        return False, "Not authenticated"
    resp = api_post(TOPUP_URL, json_data={"amount": amount}, headers=headers)
    if resp is None:
        return False, "Network error"
    if resp.status_code in (200,201):
        return True, "Top-up successful"
    try:
        return False, resp.json().get("detail", resp.text)
    except Exception:
        return False, resp.text

def queue_prediction_single(text: str, cost:int=1) -> Tuple[bool, str]:
    headers = st.session_state.get("auth_headers")
    payload = {"input_data": text, "cost": cost}
    token = st.session_state.get("token")
    if token:
        uid = decode_jwt_payload(token).get("user_id") or decode_jwt_payload(token).get("user")
        if uid:
            payload["user_id"] = uid
    resp = api_post(PREDICT_QUEUE_URL, json_data=payload, headers=headers)
    if resp is None:
        return False, "Network error"
    if resp.status_code in (200,201,202):
        try:
            j = resp.json()
            return True, j.get("message", resp.text)
        except Exception:
            return True, resp.text
    try:
        return False, resp.json().get("detail", resp.text)
    except Exception:
        return False, resp.text

def get_history() -> Tuple[bool, List[dict], str]:
    headers = st.session_state.get("auth_headers")
    if not headers:
        return False, [], "Not authenticated"
    resp = api_get(PREDICT_LIST_URL, headers=headers)
    if resp is None:
        return False, [], "Network error"
    if resp.status_code == 200:
        try:
            data = resp.json()
            return True, data if isinstance(data, list) else data.get("predictions", []), ""
        except Exception:
            return False, [], "Bad JSON from server"
    try:
        return False, [], resp.json().get("detail", resp.text)
    except Exception:
        return False, [], resp.text

# ============================
# Streamlit UI
# ============================
st.set_page_config(page_title="ML Service WebUI", layout="wide")
st.title("ML Service — Web UI")

# init session
if "token" not in st.session_state: st.session_state["token"] = None
if "auth_headers" not in st.session_state: st.session_state["auth_headers"] = None
if "profile" not in st.session_state: st.session_state["profile"] = None

# sidebar: auth + navigation
with st.sidebar:
    st.header("Навигация")
    page = st.selectbox("Страницы", ["Главная", "Predict (single)", "Batch CSV", "История", "Баланс/TopUp"])
    st.markdown("---")
    st.header("Вход / Регистрация")
    if not st.session_state["token"]:
        email = st.text_input("Email", key="login_email")
        pwd = st.text_input("Password", type="password", key="login_pwd")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Войти"):
                ok, token_or_msg = signin(email, pwd)
                if ok:
                    if token_or_msg:
                        set_token(token_or_msg)
                        st.success("Вход выполнен")
                    else:
                        st.info("Вход успешен, но токен не вернулся.")
                else:
                    st.error(f"Signin failed: {token_or_msg}")
        with col2:
            if st.button("Зарегистрироваться"):
                ok, msg = signup(email, pwd)
                if ok:
                    st.success(msg)
                else:
                    st.error(f"Signup failed: {msg}")
    else:
        st.write("Авторизован")
        if st.button("Выйти"):
            clear_token()
            st.experimental_rerun()

    st.markdown("---")
    st.markdown("Настройки API")
    st.text(API_BASE)

# ---------------------------
# Pages
# ---------------------------
if page == "Главная":
    st.header("Главная")
    st.markdown("UI для демонстрации ML-сервиса.\n- Профиль не запрашивается\n- Предсказания можно ставить сразу")
    st.write("Текущий токен:")
    st.code(st.session_state.get("token") or "не авторизован")

elif page == "Predict (single)":
    st.header("Single prediction (enqueue)")
    text = st.text_area("Текст для предсказания", value="I love this product")
    col1, col2 = st.columns(2)
    with col1:
        cost = st.number_input("Стоимость (кредиты)", min_value=0, value=1, step=1)
    with col2:
        if st.button("Отправить в очередь"):
            ok, msg = queue_prediction_single(text, cost)
            if ok:
                st.success(f"Задача поставлена: {msg}")
            else:
                st.error(f"Ошибка: {msg}")

elif page == "Batch CSV":
    st.header("Batch upload CSV (column: text)")
    uploaded = st.file_uploader("CSV файл", type=["csv"])
    default_cost = st.number_input("Cost (per item)", min_value=0, value=1, step=1)
    if uploaded:
        try:
            data = uploaded.getvalue().decode("utf-8")
            reader = csv.DictReader(StringIO(data))
            rows = list(reader)
            if not rows:
                st.warning("CSV пустой")
            else:
                st.info(f"Найдено {len(rows)} строк")
                valid = [r.get("text") or r.get("input") for r in rows if (r.get("text") or r.get("input"))]
                if st.button("Отправить все строки"):
                    ok_count, fail_count = 0, 0
                    for txt in valid:
                        ok, _ = queue_prediction_single(txt, cost=default_cost)
                        if ok: ok_count += 1
                        else: fail_count += 1
                    st.success(f"Успешно: {ok_count}, Ошибки: {fail_count}")
        except Exception as e:
            st.error(f"Ошибка парсинга CSV: {e}")

elif page == "История":
    st.header("История предсказаний")
    if not st.session_state.get("token"):
        st.info("Войдите, чтобы смотреть историю.")
    else:
        ok, data, err = get_history()
        if not ok:
            st.error(f"Ошибка: {err}")
        elif not data:
            st.info("Нет предсказаний")
        else:
            st.dataframe(data)

elif page == "Баланс/TopUp":
    st.header("Баланс и пополнение")
    if not st.session_state.get("token"):
        st.info("Войдите для пополнения.")
    else:
        amount = st.number_input("Сумма пополнения", min_value=1, value=10, step=1)
        if st.button("Пополнить"):
            ok, msg = topup(amount)
            if ok:
                st.success(msg)
            else:
                st.error(f"Ошибка: {msg}")
