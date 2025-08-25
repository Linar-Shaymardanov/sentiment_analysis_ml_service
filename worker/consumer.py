def post_result_to_api(result: Dict[str, Any]) -> None:
    """
    Преобразуем result из run_prediction в структуру, ожидаемую API,
    и POST'им её в callback endpoint приложения.
    """
    payload = {
        "user_id": result.get("user_id"),
        "model_name": result.get("model") or result.get("model_name") or "text-rule-v1",
        "input_data": result.get("input_data") or result.get("input"),
        # result должен быть dict (если строка — пробуем распарсить, иначе пустой dict)
        "result": result.get("result") if isinstance(result.get("result"), dict) else (result.get("result") or {}),
        "cost": result.get("cost", 1),
        "errors": result.get("errors", []),
        "timestamp": result.get("timestamp"),
    }

    # Если result всё-таки пришёл как строка — попробуем распарсить
    res = result.get("result")
    if isinstance(res, str):
        try:
            res = json.loads(res)
        except Exception:
            res = {}
    payload["result"] = res or {}

    headers = {"Content-Type": "application/json"}
    try:
        resp = requests.post(API_CALLBACK, json=payload, headers=headers, timeout=10)
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to POST to API callback: {e}") from e

    if not (200 <= resp.status_code < 300):
        raise RuntimeError(f"Callback returned status {resp.status_code}: {resp.text}")
