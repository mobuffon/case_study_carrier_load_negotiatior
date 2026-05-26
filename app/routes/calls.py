from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from app.auth import require_api_key
from app.db import get_session
from app.models import Call
from app.schemas import CallCreate, CallOut

router = APIRouter(
    prefix="/calls",
    tags=["calls"],
    dependencies=[Depends(require_api_key)],
)


def _dollars_to_cents(d: Optional[float]) -> Optional[int]:
    return int(round(d * 100)) if d is not None else None


def _cents_to_dollars(c: Optional[int]) -> Optional[float]:
    return round(c / 100, 2) if c is not None else None


@router.post("", response_model=CallOut, status_code=201)
def create_call(payload: CallCreate, session: Session = Depends(get_session)):
    call = Call(
        mc_number=payload.mc_number,
        carrier_name=payload.carrier_name,
        eligible=payload.eligible,
        load_id=payload.load_id,
        loadboard_rate_cents=_dollars_to_cents(payload.loadboard_rate),
        agreed_rate_cents=_dollars_to_cents(payload.agreed_rate),
        carrier_initial_offer_cents=_dollars_to_cents(payload.carrier_initial_offer),
        negotiation_rounds=payload.negotiation_rounds,
        outcome=payload.outcome,
        sentiment=payload.sentiment,
        notes=payload.notes,
        transcript_excerpt=payload.transcript_excerpt,
        duration_seconds=payload.duration_seconds,
    )
    session.add(call)
    session.commit()
    session.refresh(call)
    return _to_callout(call)


@router.get("", response_model=list[CallOut])
def list_calls(
    limit: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    stmt = select(Call).order_by(Call.created_at.desc()).limit(limit)
    calls = session.exec(stmt).all()
    return [_to_callout(c) for c in calls]


def _to_callout(c: Call) -> CallOut:
    return CallOut(
        id=c.id,
        created_at=c.created_at,
        mc_number=c.mc_number,
        carrier_name=c.carrier_name,
        eligible=c.eligible,
        load_id=c.load_id,
        loadboard_rate=_cents_to_dollars(c.loadboard_rate_cents),
        agreed_rate=_cents_to_dollars(c.agreed_rate_cents),
        negotiation_rounds=c.negotiation_rounds,
        outcome=c.outcome,
        sentiment=c.sentiment,
        notes=c.notes,
    )
