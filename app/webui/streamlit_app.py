# webui/streamlit_app.py
"""
Streamlit web UI для ML-сервиса (интеграция с FastAPI backend).
Функционал:
- регистрация / вход
- показать баланс (если backend поддерживает профиль)
- пополнение баланса (через endpoint /api/user/topup если есть)
- отправка одиночного предсказания в очередь (POST /api/predict/queue)
- массовая загрузка CSV с колонкой `text` и верификация/отправка каждой строки
- просмотр истории предсказаний (GET /api/predict/)
- админ-панель (если backend возвращает is_admin в профиле)
Настройки API вверху файла.
"""

import streamlit as st
import requests
import json
import base64
import csv
from io import StringIO, BytesIO
from typing import Optional, List, Dict

# ============================
# Настройки — поменяй при необходимости
# ============================
API_BASE = st.secrets.get("API_BASE", "http://localhost:8080")  # базовый URL back-end
SIGNUP_URL = f"{API_BASE}/api/auth/signup"
SIGNIN_URL = f"{API_BASE}/api/auth/signin"
PREDICT_QUEUE_URL = f"{API_BASE}/api/predict/queue"
PREDICT_LIST_URL = f"{API_BASE}/api/predict/"     # GET список предсказаний (user)
TOPUP_URL = f"{API_BASE}/api/user/topup"         # may be absent in your backend — обработаем ошибку
PROFILE_URL = f"{API_BASE}/api/user/me"          # optional
PREDICTION_RESULT_CALLBACK = f"{API_BASE}/api/predict/result"  # optional callback (worker -> api)
# ============================

# ---- небольшие helper-утилиты ----
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
    st.session_state["auth_headers"] = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

def clear_token():
    st.session_state.pop("token", None)
    st.session_state.pop("auth_headers", None)
    st.session_state.pop("profile", None)

def decode_jwt_payload(token: str) -> dict:
    """Декодируем payload JWT без проверки подписи (для извлечения user id/email).
       Используется только для удобства UI — не для безопасности."""
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return {}
        payload_b64 = parts[1] + "=" * ((4 - len(parts[1]) % 4) % 4)
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        return json.loads(payload_bytes)
    except Exception:
        return {}

# ---- функции взаимодействия с API ----
def signup(email: str, password: str) -> (bool, str):
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

def signin(email: str, password: str) -> (bool, Optional[str]):
    # backend может принимать form-data (OAuth2) — отправим так, т.к. более совместимо
    data = {"username": email, "password": password}
    resp = api_post(SIGNIN_URL, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    if resp is None:
        return False, None
    if resp.status_code in (200, 201):
        try:
            j = resp.json()
            token = j.get("access_token") or j.get("token") or j.get("access") or j.get("token_value")
            # Иногда сервис возвращает {cookie_name: token, token_type: 'bearer'} -> try first value
            if not token and isinstance(j, dict):
                # try first string-like value
                for v in j.values():
                    if isinstance(v, str) and v.count(".") == 2:
                        token = v
                        break
            if not token:
                # если backend вернул cookie as token field name (weird), return whole json
                st.warning("Signin response does not contain standard access_token field; saved raw response in session.")
                st.session_state["signin_raw"] = j
                return True, None
            return True, token
        except Exception:
            st.error("Unexpected signin response: " + resp.text)
            return False, None
    else:
        try:
            return False, resp.json().get("detail", resp.text)
        except Exception:
            return False, resp.text

def get_profile():
    """Попытаться получить профиль пользователя (если endpoint есть)."""
    headers = st.session_state.get("auth_headers")
    if not headers:
        return None
    resp = api_get(PROFILE_URL, headers=headers)
    if resp is None:
        return None
    if resp.status_code == 200:
        try:
            return resp.json()
        except Exception:
            return None
    return None

def topup(amount: int) -> (bool, str):
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

def queue_prediction_single(text: str, cost:int=1) -> (bool, str):
    headers = st.session_state.get("auth_headers")
    if not headers:
        return False, "Not authenticated"
    payload = {"input_data": text, "cost": cost}
    # Если backend требует user_id explicitly, попытаемся взять его из токена:
    token = st.session_state.get("token")
    if token:
        payload["user_id"] = decode_jwt_payload(token).get("user_id") or decode_jwt_payload(token).get("user")
    resp = api_post(PREDICT_QUEUE_URL, json_data=payload, headers=headers)
    if resp is None:
        return False, "Network error"
    if resp.status_code in (200,201):
        try:
            return True, resp.json().get("message", resp.text)
        except Exception:
            return True, resp.text
    try:
        return False, resp.json().get("detail", resp.text)
    except Exception:
        return False, resp.text

def get_history() -> (bool, List[dict], str):
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

# ---------------------------
# Streamlit UI
# ---------------------------
st.set_page_config(page_title="ML Service WebUI", layout="wide")
st.title("ML Service — Web UI")

# init session
if "token" not in st.session_state:
    st.session_state["token"] = None
if "auth_headers" not in st.session_state:
    st.session_state["auth_headers"] = None
if "profile" not in st.session_state:
    st.session_state["profile"] = None

# sidebar: auth + navigation
with st.sidebar:
    st.header("Навигация")
    page = st.selectbox("Страницы", ["Главная", "Predict (single)", "Batch CSV", "История", "Баланс/TopUp", "Admin (опционально)"])

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
                        # попробуем получить профиль
                        st.session_state["profile"] = get_profile()
                    else:
                        # token is None but signin returned success (possible cookie-based or raw)
                        st.info("Вход: успешный ответ, но токен не явный. Проверьте backend contract.")
                else:
                    st.error(f"Signin failed: {token_or_msg}")
        with col2:
            if st.button("Зарегистрировать"):
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
    st.caption("Если API на другом хосте — отредактируй константу API_BASE в файле webui/streamlit_app.py")

# ---------------------------
# Pages
# ---------------------------
if page == "Главная":
    st.header("Главная")
    st.markdown("""
    Простой Web-интерфейс для демонстрации работы ML-сервиса с очередями.
    Возможности:
    - регистрация/вход
    - просмотр баланса и история
    - пополнение баланса
    - отправка текстового запроса на предсказание (через очередь)
    - загрузка CSV с колонкой `text` для массовых запросов (каждая строка становится задачей)
    """)

    st.subheader("Quick checks")
    st.write("Текущий токен:")
    st.code(st.session_state.get("token") or "не авторизован")

    if st.button("Получить профиль (если backend поддерживает /api/user/me)"):
        profile = get_profile()
        if profile:
            st.json(profile)
            st.session_state["profile"] = profile
        else:
            st.warning("Профиль не получен (endpoint отсутствует или ошибка)")

elif page == "Predict (single)":
    st.header("Single prediction (enqueue)")
    text = st.text_area("Текст для предсказания", value="I love this product")
    col1, col2 = st.columns(2)
    with col1:
        cost = st.number_input("Стоимость (кредиты)", min_value=0, value=1, step=1)
    with col2:
        if st.button("Отправить в очередь"):
            if not st.session_state.get("token"):
                st.error("Сначала войдите")
            else:
                ok, msg = queue_prediction_single(text, cost)
                if ok:
                    st.success(f"Задача поставлена: {msg}")
                else:
                    st.error(f"Ошибка при постановке: {msg}")

elif page == "Batch CSV":
    st.header("Batch upload CSV (колонка `text`)")
    st.markdown("Загрузите CSV с колонкой `text`. Каждая строка будет проверена локально и отправлена в очередь.")
    uploaded = st.file_uploader("CSV файл", type=["csv"])
    default_cost = st.number_input("Cost (per item)", min_value=0, value=1, step=1)
    if uploaded:
        try:
            data = uploaded.getvalue().decode("utf-8")
            csvf = StringIO(data)
            reader = csv.DictReader(csvf)
            rows = list(reader)
            if len(rows) == 0:
                st.warning("CSV пустой или не содержит строчек")
            else:
                st.info(f"Найдено {len(rows)} строк")
                invalid = []
                valid = []
                for i, r in enumerate(rows, start=1):
                    txt = (r.get("text") or r.get("input") or "").strip()
                    if not txt:
                        invalid.append((i, r))
                    else:
                        valid.append(txt)
                st.write(f"Valid: {len(valid)}, Invalid (missing text): {len(invalid)}")
                if invalid:
                    st.dataframe({"row": [i for i, _ in invalid], "raw": [r for _, r in invalid]})
                if st.button("Отправить валидные строки в очередь"):
                    if not st.session_state.get("token"):
                        st.error("Выполните вход")
                    else:
                        results = {"ok":0, "fail":0, "errors":[]}
                        for txt in valid:
                            ok, msg = queue_prediction_single(txt, cost=default_cost)
                            if ok:
                                results["ok"] += 1
                            else:
                                results["fail"] += 1
                                results["errors"].append(msg)
                        st.success(f"Отправлено: {results['ok']}, Ошибок: {results['fail']}")
                        if results["errors"]:
                            st.write(results["errors"])
        except Exception as e:
            st.error(f"Failed to parse CSV: {e}")

elif page == "История":
    st.header("История предсказаний")
    if not st.session_state.get("token"):
        st.info("Войдите, чтобы смотреть историю")
    else:
        ok, data, err = get_history()
        if not ok:
            st.error(f"Ошибка: {err}")
        else:
            if not data:
                st.info("Нет предсказаний")
            else:
                # ожидаем список объектов; попробуем нормализовать вывод
                st.write(f"Найдено {len(data)} записей")
                st.dataframe(data)

elif page == "Баланс/TopUp":
    st.header("Баланс и пополнение")
    prof = st.session_state.get("profile")
    if not prof:
        if st.session_state.get("token"):
            prof = get_profile()
            if prof:
                st.session_state["profile"] = prof
    if prof:
        st.subheader("Профиль")
        st.json(prof)
        # пополнение
        amount = st.number_input("Сумма пополнения", min_value=1, value=10, step=1)
        if st.button("Пополнить баланс"):
            ok, msg = topup(amount)
            if ok:
                st.success(msg)
                st.session_state["profile"] = get_profile()
            else:
                st.error(f"Topup failed: {msg}")
    else:
        st.info("Профиль не доступен. Если backend не поддерживает /api/user/me, то баланс не отображается в UI.")

elif page == "Admin (опционально)":
    st.header("Admin (опционально)")
    st.markdown("Если у вас есть роль администратора, тут можно добавить админские функции (пополнить баланс юзеру, просмотреть все транзакции).")
    if not st.session_state.get("token"):
        st.info("Войдите как админ")
    else:
        prof = st.session_state.get("profile") or get_profile()
        if prof and prof.get("is_admin"):
            st.success("Detected admin in profile")
            # simple admin action: manual top-up by admin to another user via API (endpoint должен быть реализован)
            user_email = st.text_input("Email пользователя для пополнения", key="admin_email")
            admin_amount = st.number_input("Amount to credit", min_value=1, value=10, step=1, key="admin_amount")
            if st.button("Credit user (admin)"):
                # API for admin credit may differ; we'll try /api/admin/topup or /api/user/topup?admin=true
                hdr = st.session_state.get("auth_headers")
                # Try admin endpoint variations
                tried = []
                success = False
                for url in [f"{API_BASE}/api/admin/topup", f"{API_BASE}/api/user/topup?admin=true", f"{API_BASE}/api/user/topup_admin"]:
                    tried.append(url)
                    resp = api_post(url, json_data={"email": user_email, "amount": admin_amount}, headers=hdr)
                    if resp and resp.status_code in (200,201):
                        st.success("Пополнение выполнено")
                        success = True
                        break
                if not success:
                    st.error("Не удалось выполнить. Попробуй реализовать админ-ендпоинт на бэкенде.")
        else:
            st.warning("Вы не админ или профиль не содержит is_admin=true.")
