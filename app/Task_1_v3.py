# app/Task_1_v3.py
"""
Task_1_v3: Entities + lightweight text 'ML' model for quick predictions.

Этот файл содержит:
- исходные dataclass'ы (User, Balance, TransactionRecord, PredictionRecord и т.д.)
- лёгкую rule-based текстовую модель TextClassificationModel
- вспомогательную функцию run_prediction(payload) для использования в worker
"""

from dataclasses import dataclass, field
from typing import List, Optional, Protocol, Dict, Any
from datetime import datetime, timezone
import os
import re
import json

# --------------------
# Исключения
# --------------------
class ValidationError(Exception):
    pass

class InsufficientBalanceError(Exception):
    pass

# --------------------
# 1. Баланс и пользователь
# --------------------
@dataclass
class Balance:
    credits: int = 0

    def add(self, amount: int) -> None:
        if amount <= 0:
            raise ValidationError("Сумма пополнения должна быть > 0")
        self.credits += amount

    def subtract(self, amount: int) -> None:
        if amount <= 0:
            raise ValidationError("Списание должно быть > 0")
        if self.credits < amount:
            raise InsufficientBalanceError("Недостаточно средств")
        self.credits -= amount

@dataclass
class User:
    id: int
    email: str
    _password: str
    balance: Balance = field(default_factory=Balance)
    is_admin: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        self._validate_email()
        self._validate_password()

    def _validate_email(self) -> None:
        pattern = re.compile(r'^[\w\.-]+@[\w\.-]+\.\w+$')
        if not pattern.match(self.email):
            raise ValidationError("Неправильный формат email")

    def _validate_password(self) -> None:
        if len(self._password) < 6:
            raise ValidationError("Пароль должен быть минимум 6 символов")

    def check_password(self, pw: str) -> bool:
        return self._password == pw

    def top_up(self, amount: int) -> 'TransactionRecord':
        self.balance.add(amount)
        return TransactionRecord(
            id=-1,
            user_id=self.id,
            amount=amount,
            description="Пополнение баланса",
            timestamp=datetime.now(timezone.utc)
        )

    def charge(self, amount: int, description: Optional[str] = None) -> 'TransactionRecord':
        self.balance.subtract(amount)
        return TransactionRecord(
            id=-1,
            user_id=self.id,
            amount=-abs(amount),
            description=description or "Списание за услугу",
            timestamp=datetime.now(timezone.utc)
        )

# --------------------
# 2. Транзакция
# --------------------
@dataclass
class TransactionRecord:
    id: int
    user_id: int
    amount: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    description: Optional[str] = None

# --------------------
# 3. Prediction record
# --------------------
@dataclass
class PredictionRecord:
    id: int
    user_id: int
    model_name: str
    input_meta: str
    result_json: Optional[Dict[str, Any]]
    cost: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    errors: List[str] = field(default_factory=list)

# --------------------
# 4. ML Model Protocol + text rule-based model
# --------------------
class MLModel(Protocol):
    name: str

    def validate(self, data: Any) -> List[str]:
        ...

    def predict(self, data: Any) -> Dict[str, Any]:
        ...

@dataclass
class TextClassificationModel:
    name: str = "text-rule-v1"
    positive_tokens: List[str] = field(default_factory=lambda: [
        "good", "great", "love", "excellent", "awesome", "nice", "amazing", "best", "like", "happy"
    ])
    negative_tokens: List[str] = field(default_factory=lambda: [
        "bad", "terrible", "hate", "worst", "awful", "dislike", "sad", "angry", "problem", "disappointed"
    ])
    neutral_threshold: float = 0.1

    def validate(self, data: Any) -> List[str]:
        errors = []
        if not isinstance(data, str):
            errors.append("input must be a string")
        elif not data.strip():
            errors.append("input text is empty")
        return errors

    def predict(self, data: str) -> Dict[str, Any]:
        # very small rule-based scoring:
        txt = data.lower()
        pos = sum(txt.count(tok) for tok in self.positive_tokens)
        neg = sum(txt.count(tok) for tok in self.negative_tokens)

        total = pos + neg
        # Raw score in [-1,1]
        if total == 0:
            score = 0.5  # neutral baseline -> score 0.5
        else:
            # normalized to [0,1], positive bias
            score = (pos / total) if total > 0 else 0.5
            # map to [0,1] with some smoothing
            score = round(0.25 + 0.75 * score, 3)  # ensure not 0.0

        if total == 0 or abs(pos - neg) / (total if total else 1) < self.neutral_threshold:
            sentiment = "neutral"
        else:
            sentiment = "positive" if pos > neg else "negative"

        return {
            "model": self.name,
            "sentiment": sentiment,
            "score": float(score),
            "pos_count": pos,
            "neg_count": neg,
        }

# --------------------
# 5. Helper: run_prediction(payload)
# --------------------
def run_prediction(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    payload expected keys:
      - user_id: int
      - input_data: str
      - cost: Optional[int] (worker will use if present; otherwise default=1)
      - model: Optional[str]
    Returns a dict suitable to POST to API callback:
    { "user_id": ..., "input_data": ..., "result": {...}, "cost": ... }
    """
    # Basic validation
    if not isinstance(payload, dict):
        raise ValidationError("payload must be a dict")
    if "user_id" not in payload:
        raise ValidationError("missing user_id")
    if "input_data" not in payload:
        raise ValidationError("missing input_data")
    user_id = int(payload["user_id"])
    input_data = payload["input_data"]
    cost = int(payload.get("cost", 1))

    # choose model (only text model supported here)
    model_name = payload.get("model", "text-rule-v1")
    model = TextClassificationModel()

    errors = model.validate(input_data)
    result = None
    if not errors:
        result = model.predict(input_data)

    response = {
        "user_id": user_id,
        "input_data": str(input_data),
        "result": result,
        "cost": cost,
        "model": model_name,
        "errors": errors,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return response

# --------------------
# 6. Quick demo when run directly
# --------------------
if __name__ == "__main__":
    sample = {"user_id": 1, "input_data": "I love this product, it's the best!", "cost": 1}
    out = run_prediction(sample)
    print("Preview prediction:", json.dumps(out, indent=2, ensure_ascii=False))
