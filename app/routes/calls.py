from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.auth import require_api_key
from app.calls_helpers import enrich_call
from app.db import get_session
from app.models import Call
from app.schemas import CallCreate, CallDetailOut, CallOut

router = APIRouter(
    prefix="/calls",
    tags=["calls"],
    dependencies=[Depends(require_api_key)],
)


def _dollars_to_cents(d: Optional[float]) -> Optional[int]:
    return int(round(d * 100)) if d is not None else None


@router.post("", response_model=CallOut, status_code=201)
def create_call(payload: CallCreate, session: Session = Depends(get_session)):
    call = Call(
        mc_number=payload.mc_number,
        carrier_name=payload.carrier_name,
        eligible=payload.eligible,
        load_id=payload.load_id,
        loadboard_rate_cents=_dollars_to_cents(payload.loadboard_rate),
        agreed_rate_cents=_dollars_to_cents(payload.agreed_rate),
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
    return CallOut(**enrich_call(call))


@router.get("", response_model=list[CallOut])
def list_calls(
    limit: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    stmt = select(Call).order_by(Call.created_at.desc()).limit(limit)
    calls = session.exec(stmt).all()
    return [CallOut(**enrich_call(c)) for c in calls]


@router.get("/{call_id}", response_model=CallDetailOut)
def get_call(call_id: int, session: Session = Depends(get_session)):
    call = session.get(Call, call_id)
    if not call:
        raise HTTPException(status_code=404, detail=f"Call {call_id} not found")
    return CallDetailOut(**enrich_call(call, include_transcript=True))
