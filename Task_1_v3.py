# Task_1_v3.py
from dataclasses import dataclass, field
from typing import List, Optional, Protocol, Dict, Any
from datetime import datetime, timezone
import os
import re

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
    """
    Пользователь системы.
    """
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
        """
        Пополнение баланса — возвращает объект TransactionRecord для записи в историю.
        """
        self.balance.add(amount)
        return TransactionRecord(
            id=-1,
            user_id=self.id,
            amount=amount,
            description="Пополнение баланса",
            timestamp=datetime.now(timezone.utc)
        )

    def charge(self, amount: int, description: Optional[str] = None) -> 'TransactionRecord':
        """
        Списание с баланса — возвращает объект TransactionRecord.
        amount должен быть положительным, в записи хранится отрицательное значение.
        """
        self.balance.subtract(amount)
        return TransactionRecord(
            id=-1,
            user_id=self.id,
            amount=-abs(amount),
            description=description or "Списание за услугу",
            timestamp=datetime.now(timezone.utc)
        )

# --------------------
# 2. Транзакция — запись в истории транзакций
# --------------------
@dataclass
class TransactionRecord:
    """
    Отдельная сущность истории транзакций.
    id: int - идентификатор (для БД или логов)
    user_id: int - пользователь
    amount: int - положительное = пополнение, отрицательное = списание
    timestamp: datetime - время транзакции (UTC-aware)
    description: Optional[str] - текст описания
    """
    id: int
    user_id: int
    amount: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    description: Optional[str] = None

# --------------------
# 3. Интерфейс ML-модели и конкретная модель (изображения/текста можно менять)
# --------------------
class MLModel(Protocol):
    name: str

    def validate(self, data: Any) -> List[str]:
        ...

    def predict(self, data: Any) -> Dict[str, Any]:
        ...

@dataclass
class ImageClassificationModel:
    name: str = "imgcls-v1"
    labels: List[str] = field(default_factory=lambda: ["cat", "dog", "car", "tree"])

    def validate(self, data: bytes) -> List[str]:
        if not data:
            return ["Пустые данные"]
        return []

    def predict(self, data: bytes) -> Dict[str, Any]:
        if not data:
            raise ValidationError("Empty image data")
        idx = data[0] % len(self.labels)
        return {
            "model": self.name,
            "predicted_label": self.labels[idx],
            "confidence": round(0.5 + (idx / (2 * len(self.labels))), 2),
        }

# --------------------
# 4. Request / Job для классификации изображения
# --------------------
@dataclass
class ClassificationRequest:
    id: int
    user: User
    model: MLModel
    image_path: str
    cost_per_image: int = 5
    result: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        self._validate_image_path()

    def _validate_image_path(self) -> None:
        if not os.path.isfile(self.image_path):
            raise ValidationError(f"Файл не найден: {self.image_path}")

    def compute_cost(self) -> int:
        return self.cost_per_image

    def execute(self) -> 'PredictionRecord':
        """
        Выполнить задачу классификации:
        - валидировать вход (model.validate)
        - вычислить стоимость
        - списать с баланса пользователя (user.charge)
        - если нет ошибок — выполнить predict
        - сформировать и вернуть PredictionRecord
        """
        # 1) читаем данные и валидируем
        with open(self.image_path, "rb") as f:
            data = f.read()
        errors = self.model.validate(data)

        # 2) вычисляем стоимость
        cost = self.compute_cost()

        # 3) списание (если недостаточно будет выброшено исключение)
        tx = self.user.charge(cost, description=f"Списание за классификацию (req_id={self.id})")

        # 4) predict (только если нет ошибок)
        result = None
        if not errors:
            result = self.model.predict(data)
            self.result = result

        # 5) формируем запись предсказания
        pred = PredictionRecord(
            id=-1,
            user_id=self.user.id,
            model_name=self.model.name,
            input_path=self.image_path,
            errors=errors,
            result=result,
            cost=cost,
            timestamp=self.timestamp,
        )
        return pred

# --------------------
# 5. История предсказаний
# --------------------
@dataclass
class PredictionRecord:
    """
    Отдельная сущность истории предсказаний.
    id: int
    user_id: int
    model_name: str
    input_path: str
    errors: List[str] - ошибки валидации (если есть)
    result: Optional[dict] - результат предсказания (None если ошибок)
    cost: int - списанные кредиты
    timestamp: datetime (UTC-aware)
    """
    id: int
    user_id: int
    model_name: str
    input_path: str
    errors: List[str]
    result: Optional[Dict[str, Any]]
    cost: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

# --------------------
# 6. Небольшой пример использования (при запуске как скрипт)
# --------------------
if __name__ == "__main__":
    # Демонстрация работы сущностей (без БД)
    user = User(id=1, email="test@mail.ru", _password="password123", balance=Balance(credits=50))
    model = ImageClassificationModel()

    # Показать текущие значения и timezone-aware дату
    print("Task_1_v3 loaded. Entities: User, Balance, TransactionRecord, PredictionRecord, ClassificationRequest")
    print(f"User created_at (UTC): {user.created_at.isoformat()}")
    # Примечание: execute требует реального файла на диске, поэтому здесь мы не вызываем execute.

