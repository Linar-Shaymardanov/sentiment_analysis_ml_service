# app/scripts/init_db.py
from app.database.database import init_db, get_database_engine
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select
from app.models.user import User
from app.models.prediction import Prediction
import json

# правильные импорты из сервисов (по фактическим файлам у тебя)
from app.services.crud.user import create_user, add_credits, charge_credits
from app.services.crud.transaction import get_transactions_for_user
from app.services.crud.prediction import create_prediction as create_prediction_record, get_predictions_for_user

def seed_and_test(drop_all: bool = True):
    init_db(drop_all=drop_all)
    engine = get_database_engine()
    with Session(engine) as session:
        # Demo users
        demo = User(email="demo@user.com", password="password123", credits=100, is_admin=False)
        admin = User(email="admin@user.com", password="password123", credits=0, is_admin=True)
        for u in (demo, admin):
            try:
                create_user(u, session)
            except IntegrityError:
                session.rollback()

        # fetch demo user
        demo_db = session.exec(select(User).where(User.email == "demo@user.com")).first()
        print("Demo user:", demo_db)

        # top up (используем add_credits)
        tx1 = add_credits(demo_db.id, 50, session)
        print("Top up tx:", tx1)

        # charge (используем charge_credits)
        tx2 = charge_credits(demo_db.id, 30, session)
        print("Charge tx:", tx2)

        # create prediction record
        # У нас create_prediction в services принимает объект Prediction (см. app/services/crud/prediction.py)
        pred_obj = Prediction(
            user_id=demo_db.id,
            model_name="stub-model",
            input_meta="I love this!",
            result_json=json.dumps({"sentiment": "positive", "score": 0.92})
        )

        pred = create_prediction_record(pred_obj, session)
        print("Prediction created:", pred)

        # list transactions & predictions
        txs = get_transactions_for_user(demo_db.id, session)
        preds = get_predictions_for_user(demo_db.id, session)
        print(f"User {demo_db.email} credits: {demo_db.credits}")
        print("Transactions:", txs)
        print("Predictions:", preds)

if __name__ == "__main__":
    seed_and_test(drop_all=True)
