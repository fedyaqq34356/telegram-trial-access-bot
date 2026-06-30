"""Демо-данные для просмотра интерфейса. Запуск: python seed_demo.py
Удалить демо: python seed_demo.py --clear
"""
import random
import sys
from datetime import datetime, timezone, timedelta

from app.database import SessionLocal, engine, Base
from app.models import Agency, Host, SplitOperation, ActionLog

Base.metadata.create_all(bind=engine)

DEMO_AGENCIES = ["Agency1", "Agency2", "Agency3"]
NAMES = ["Lana", "Mia", "Sofia", "Emma", "Olivia", "Amelia", "Jane", "Ava", "Isla", "Aria",
         "Nora", "Luna", "Ella", "Mila", "Zoe", "Ruby", "Ivy", "Hazel", "Chloe", "Lily"]
ONLINE = ["2ч 45м", "1ч 20м", "3ч 10м", "0ч 40м", "4ч 50м", "1ч 55м", "5ч 05м"]
MONTH_ONLINE = ["89ч 20м", "40ч 10м", "55ч 30м", "102ч 15м", "12ч 05м", "33ч 40м"]

def clear(db):
    db.query(Host).delete()
    db.query(SplitOperation).delete()
    db.query(ActionLog).delete()
    for a in db.query(Agency).filter(Agency.name.in_(DEMO_AGENCIES)).all():
        db.delete(a)
    db.commit()
    print("Демо-данные удалены.")

def seed(db):
    clear(db)
    agencies = []
    for name in DEMO_AGENCIES:
        a = db.query(Agency).filter(Agency.name == name).first()
        if not a:
            a = Agency(name=name, url="https://admin.livegirl.me", is_active=True,
                       last_synced_at=datetime.now(timezone.utc))
            db.add(a)
        agencies.append(a)
    db.commit()

    for a in agencies:
        n = random.randint(6, 10)
        for i in range(n):
            monthly = random.choice([
                random.randint(200, 1900), random.randint(2000, 6999),
                random.randint(7000, 19999), random.randint(20000, 44999),
                random.randint(45000, 90000),
            ])
            real_rate = round(random.uniform(0.05, 0.30), 2)
            name = random.choice(NAMES) + random.choice(["", "_", str(random.randint(1, 99))])
            db.add(Host(
                agency_id=a.id,
                display_account_id=str(random.randint(10000000, 99999999)),
                nickname=name,
                avatar_url="",
                agent_name=a.name,
                ratio=random.choice([1000, 1200, 1500, 1800, 2000]),
                down_rate=round(random.uniform(0.05, 0.25), 2),
                real_down_rate=real_rate,
                receive_rate=round(random.uniform(0.1, 0.45), 2),
                monthly_income=monthly,
                weekly_income=int(monthly / 4),
                last_day_income=random.randint(200, 3000),
                monthly_online=random.choice(MONTH_ONLINE),
                last_day_online=random.choice(ONLINE),
                balance_coins=random.randint(0, 5000),
                split_diamond=random.choice([0, 50, 99, 150, 320, 800]),
                monthly_income_ranking=random.randint(1, 500),
                ban_status="2",
            ))
    db.commit()

    for i, a in enumerate(agencies):
        db.add(SplitOperation(
            scope_label=a.name, agency_id=a.id, processed=random.randint(40, 120),
            skipped=random.randint(5, 30), errors=random.randint(0, 3),
            total_amount_coins=random.randint(5000, 40000), status=random.choice(["done", "partial"]),
            started_at=datetime.now(timezone.utc) - timedelta(hours=i + 1),
            finished_at=datetime.now(timezone.utc), duration_seconds=round(random.uniform(20, 90), 1),
            details="{}",
        ))
    db.add(SplitOperation(
        scope_label="Все агентства", agency_id=None, processed=156, skipped=28, errors=0,
        total_amount_coins=32450, status="done",
        started_at=datetime.now(timezone.utc) - timedelta(minutes=40),
        finished_at=datetime.now(timezone.utc), duration_seconds=72.5, details="{}",
    ))

    for at, msg in [
        ("ratio_change", ""), ("split", "Запущен Split"), ("sync", "Обновление данных"),
        ("ratio_change", ""), ("login", "Вход в систему"),
    ]:
        db.add(ActionLog(username="admin", action_type=at, agency_name=random.choice(DEMO_AGENCIES),
                         anchor_id=str(random.randint(10000000, 99999999)),
                         old_value="20", new_value="18", status="done", message=msg,
                         created_at=datetime.now(timezone.utc) - timedelta(minutes=random.randint(1, 200))))
    db.commit()
    total = db.query(Host).count()
    print(f"Готово: {len(agencies)} агентства, {total} девушек, история Split и журнал засеяны.")

if __name__ == "__main__":
    db = SessionLocal()
    try:
        if "--clear" in sys.argv:
            clear(db)
        else:
            seed(db)
    finally:
        db.close()
