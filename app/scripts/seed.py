# app/scripts/seed.py
from sqlmodel import Session, select
from app.database.database import engine
from app.models.user import User

def seed():
    with Session(engine) as session:
        exists = session.exec(select(User)).first()
        if exists:
            print("Seed: users exist, skipping")
            return
        demo = User(email="demo@example.com", password="demo", is_admin=True, credits=100)
        session.add(demo)
        session.commit()
        print("Seeded demo user")

if __name__ == "__main__":
    seed()
