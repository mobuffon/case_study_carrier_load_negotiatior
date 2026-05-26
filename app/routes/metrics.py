from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.auth import require_api_key
from app.db import get_session
from app.models import Call
from app.schemas import MetricsSummary

router = APIRouter(
    prefix="/metrics",
    tags=["metrics"],
    dependencies=[Depends(require_api_key)],
)


@router.get("/summary", response_model=MetricsSummary)
def summary(session: Session = Depends(get_session)):
    calls = session.exec(select(Call)).all()
    total = len(calls)

    if total == 0:
        return MetricsSummary(
            total_calls=0,
            booked_count=0,
            conversion_rate=0.0,
            avg_negotiation_rounds=0.0,
            avg_rate_delta_dollars=0.0,
            avg_rate_delta_pct=0.0,
            outcome_breakdown={},
            sentiment_breakdown={},
            eligibility_rate=0.0,
        )

    booked = [c for c in calls if c.outcome == "booked"]
    booked_with_rates = [
        c
        for c in booked
        if c.agreed_rate_cents is not None and c.loadboard_rate_cents is not None
    ]

    avg_rounds = sum(c.negotiation_rounds for c in calls) / total

    if booked_with_rates:
        deltas_cents = [
            c.agreed_rate_cents - c.loadboard_rate_cents for c in booked_with_rates
        ]
        avg_delta_cents = sum(deltas_cents) / len(deltas_cents)
        avg_delta_dollars = round(avg_delta_cents / 100, 2)
        avg_delta_pct = round(
            sum(
                (c.agreed_rate_cents - c.loadboard_rate_cents) / c.loadboard_rate_cents
                for c in booked_with_rates
            )
            / len(booked_with_rates)
            * 100,
            2,
        )
    else:
        avg_delta_dollars = 0.0
        avg_delta_pct = 0.0

    outcome_breakdown: dict[str, int] = {}
    for c in calls:
        outcome_breakdown[c.outcome] = outcome_breakdown.get(c.outcome, 0) + 1

    sentiment_breakdown: dict[str, int] = {}
    for c in calls:
        sentiment_breakdown[c.sentiment] = sentiment_breakdown.get(c.sentiment, 0) + 1

    verified = [c for c in calls if c.eligible is not None]
    eligibility_rate = (
        sum(1 for c in verified if c.eligible) / len(verified) if verified else 0.0
    )

    return MetricsSummary(
        total_calls=total,
        booked_count=len(booked),
        conversion_rate=round(len(booked) / total, 4),
        avg_negotiation_rounds=round(avg_rounds, 2),
        avg_rate_delta_dollars=avg_delta_dollars,
        avg_rate_delta_pct=avg_delta_pct,
        outcome_breakdown=outcome_breakdown,
        sentiment_breakdown=sentiment_breakdown,
        eligibility_rate=round(eligibility_rate, 4),
    )
