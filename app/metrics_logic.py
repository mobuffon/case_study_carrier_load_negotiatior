from sqlmodel import Session, select

from app.calls_helpers import decline_reason_from_call
from app.db import get_engine
from app.models import Call
from app.schemas import MetricsSummary


def compute_metrics_summary(calls: list[Call]) -> MetricsSummary:
    total = len(calls)
    if total == 0:
        return MetricsSummary(
            total_calls=0,
            booked_count=0,
            conversion_rate=0.0,
            avg_negotiation_rounds=0.0,
            avg_rate_delta_dollars=0.0,
            avg_rate_delta_pct=0.0,
            avg_listed_rate=0.0,
            avg_agreed_rate=0.0,
            negotiation_efficiency=0.0,
            outcome_breakdown={},
            sentiment_breakdown={},
            decline_reason_breakdown={},
            eligibility_rate=0.0,
        )

    booked = [c for c in calls if c.outcome == "booked"]
    booked_with_rates = [
        c
        for c in booked
        if c.agreed_rate_cents is not None and c.loadboard_rate_cents is not None
    ]

    avg_rounds = (
        sum(c.negotiation_rounds for c in booked) / len(booked) if booked else 0.0
    )

    if booked_with_rates:
        deltas_cents = [
            c.agreed_rate_cents - c.loadboard_rate_cents for c in booked_with_rates
        ]
        avg_delta_cents = sum(deltas_cents) / len(booked_with_rates)
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
        avg_listed = round(
            sum(c.loadboard_rate_cents for c in booked_with_rates)
            / len(booked_with_rates)
            / 100,
            2,
        )
        avg_agreed = round(
            sum(c.agreed_rate_cents for c in booked_with_rates)
            / len(booked_with_rates)
            / 100,
            2,
        )
        at_or_above_floor = sum(
            1
            for c in booked_with_rates
            if c.agreed_rate_cents >= int(c.loadboard_rate_cents * 0.98)
        )
        negotiation_efficiency = round(at_or_above_floor / len(booked_with_rates), 4)
    else:
        avg_delta_dollars = 0.0
        avg_delta_pct = 0.0
        avg_listed = 0.0
        avg_agreed = 0.0
        negotiation_efficiency = 0.0

    outcome_breakdown: dict[str, int] = {}
    sentiment_breakdown: dict[str, int] = {}
    decline_reason_breakdown: dict[str, int] = {}

    for c in calls:
        outcome_breakdown[c.outcome] = outcome_breakdown.get(c.outcome, 0) + 1
        sentiment_breakdown[c.sentiment] = sentiment_breakdown.get(c.sentiment, 0) + 1
        if c.outcome in ("declined", "no_agreement"):
            reason = decline_reason_from_call(c)
            decline_reason_breakdown[reason] = decline_reason_breakdown.get(reason, 0) + 1

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
        avg_listed_rate=avg_listed,
        avg_agreed_rate=avg_agreed,
        negotiation_efficiency=negotiation_efficiency,
        outcome_breakdown=outcome_breakdown,
        sentiment_breakdown=sentiment_breakdown,
        decline_reason_breakdown=decline_reason_breakdown,
        eligibility_rate=round(eligibility_rate, 4),
    )
