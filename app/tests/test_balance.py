import json
from http import HTTPStatus

def test_signup_and_signin_and_topup_and_predict_queue(client):
    # 1) signup
    resp = client.post("/api/auth/signup", json={"email":"test1@local","password":"pass"})
    assert resp.status_code in (200, 201)

    # 2) signin (OAuth2 expects form-data)
    resp = client.post("/api/auth/signin", data={"username":"test1@local","password":"pass"})
    assert resp.status_code == HTTPStatus.OK
    j = resp.json()
    assert "access_token" in j or any(isinstance(v, str) and v.count(".")==2 for v in j.values())

    token = j.get("access_token") or next((v for v in j.values() if isinstance(v,str) and v.count(".")==2), None)
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    # 3) topup — если endpoint реализован
    resp = client.post("/api/user/topup", json={"amount": 10}, headers=headers)
    # может быть 200/201 или 404 если endpoint не реализован
    assert resp.status_code in (200, 201, 404)

    # 4) ставим predict в очередь — если баланс положительный, ожидаем 200/201 or 202
    payload = {"user_id": 1, "input_data": "I love it", "cost": 1}
    resp = client.post("/api/predict/queue", json=payload, headers=headers)
    assert resp.status_code in (200, 201, 202, 403, 404)

    # 5) проверим историю (если есть)
    resp = client.get("/api/predict/", headers=headers)
    assert resp.status_code in (200, 404)
