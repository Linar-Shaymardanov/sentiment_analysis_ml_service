# app/scripts/init_db.py
from app.database.database import init_db, get_database_engine
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select
from app.models.user import User
from app.services.crud.user import create_user, top_up_user, charge_user, create_prediction, get_transactions_for_user, get_predictions_for_user

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

        # top up
        tx1 = top_up_user(demo_db.id, 50, session, description="Initial topup")
        print("Top up tx:", tx1)

        # charge
        tx2 = charge_user(demo_db.id, 30, session, description="Run prediction")
        print("Charge tx:", tx2)

        # create prediction record
        pred = create_prediction(demo_db.id, input_data="I love this!", result={"sentiment": "positive", "score": 0.92}, cost=10, session=session)
        print("Prediction created:", pred)

        # list transactions & predictions
        txs = get_transactions_for_user(demo_db.id, session)
        preds = get_predictions_for_user(demo_db.id, session)
        print(f"User {demo_db.email} credits: {demo_db.credits}")
        print("Transactions:", txs)
        print("Predictions:", preds)

if __name__ == "__main__":
    seed_and_test(drop_all=True)
