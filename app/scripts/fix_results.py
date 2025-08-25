# app/scripts/fix_results.py
import json
from sqlmodel import Session, select
from app.database.database import engine
from app.models.prediction import Prediction

def main():
    updated = 0
    with Session(engine) as session:
        rows = session.exec(select(Prediction)).all()
        for p in rows:
            if isinstance(p.result, str):
                raw = p.result
                try:
                    parsed = json.loads(raw)
                    p.result = parsed
                    session.add(p)
                    updated += 1
                    print(f"Updated prediction id={p.id}")
                except Exception as e:
                    print(f"Skipping id={p.id} — cannot parse result: {e}")
        if updated:
            session.commit()
    print("Done. Updated rows:", updated)

if __name__ == "__main__":
    main()
