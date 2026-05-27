"""Seed demo call records. Run: python -m app.seed_calls"""
from datetime import datetime, timedelta

from sqlmodel import Session, delete

from app.db import get_engine, init_db
from app.loads import load_loads_from_csv
from app.models import Call

DAY_OFFSETS = [0, 0, 1, 2, 3, 4, 5, 7, 8, 10, 12, 14, 16, 18, 22]

SEED_CALLS = [
    ("021708", "CARR TRANSPORTATION LLC", True, "L-1001", 1850, 1800, 2, "booked", "positive", 142, None),
    ("193474", "Schneider National", True, "L-1003", 1650, None, 3, "no_agreement", "negative", 198, "rate too high"),
    ("107012", "Werner Enterprises", True, "L-1007", 1250, 1250, 0, "booked", "neutral", 95, None),
    ("334521", "Swift Transportation", False, None, None, None, 0, "not_eligible", "neutral", 45, None),
    ("556789", "Heartland Express", True, "L-1005", 800, None, 0, "declined", "neutral", 62, "not interested"),
    ("021708", "CARR TRANSPORTATION LLC", True, "L-1013", 1350, 1320, 1, "booked", "positive", 118, None),
    ("778342", "Old Dominion Freight", True, None, None, None, 0, "no_match", "neutral", 88, None),
    ("445612", "Estes Express", True, "L-1008", 1050, None, 3, "no_agreement", "negative", 175, "rate too high"),
    ("193474", "Schneider National", True, "L-1002", 1400, 1370, 2, "booked", "positive", 156, None),
    ("901234", None, False, None, None, None, 0, "not_eligible", "negative", 38, None),
    ("334521", "Swift Transportation", True, "L-1011", 750, 750, 0, "booked", "positive", 72, None),
    ("667890", "USF Holland", True, "L-1004", 950, None, 0, "declined", "neutral", 55, "timing"),
    ("107012", "Werner Enterprises", True, "L-1014", 1450, 1425, 1, "booked", "positive", 134, None),
    ("223344", "Averitt Express", True, "L-1009", 650, None, 3, "no_agreement", "negative", 189, "rate too high"),
    ("556789", "Heartland Express", True, "L-1015", 1100, 1065, 2, "booked", "neutral", 167, None),
]


def seed_calls_if_empty() -> int:
    from sqlmodel import Session, func, select

    with Session(get_engine()) as session:
        count = session.exec(select(func.count()).select_from(Call)).one()
        if count:
            return 0
    return seed_calls()


def seed_calls() -> int:
    init_db()
    load_loads_from_csv()
    engine = get_engine()
    now = datetime.utcnow()

    with Session(engine) as session:
        session.exec(delete(Call))
        session.commit()

        for i, row in enumerate(SEED_CALLS):
            mc, carrier, eligible, load_id, lb, agreed, rounds, outcome, sentiment, duration, notes = row
            created = now - timedelta(days=DAY_OFFSETS[i], hours=(i * 3) % 24 + 1)
            session.add(
                Call(
                    created_at=created,
                    mc_number=mc,
                    carrier_name=carrier,
                    eligible=eligible,
                    load_id=load_id,
                    loadboard_rate_cents=int(lb * 100) if lb is not None else None,
                    agreed_rate_cents=int(agreed * 100) if agreed is not None else None,
                    negotiation_rounds=rounds,
                    outcome=outcome,
                    sentiment=sentiment,
                    duration_seconds=duration,
                    notes=notes,
                )
            )
        session.commit()
    return len(SEED_CALLS)


if __name__ == "__main__":
    count = seed_calls()
    print(f"Seeded {count} calls (replaced all existing records).")
