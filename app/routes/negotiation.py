from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth import require_api_key
from app.negotiation import compute_negotiation
from app.schemas import NegotiationResponse

router = APIRouter(
    prefix="/negotiation",
    tags=["negotiation"],
    dependencies=[Depends(require_api_key)],
)


@router.get("/counter", response_model=NegotiationResponse)
def negotiation_counter(
    loadboard_rate: float = Query(..., description="Listed loadboard rate in dollars"),
    our_offer: float = Query(..., description="Your current offer in dollars"),
    carrier_counter: float = Query(..., description="Carrier's counter in dollars"),
    round: int = Query(..., ge=1, le=3, description="Negotiation round (1–3)"),
):
    """
    Deterministic next negotiation move with spoken dollar amounts.

    Call on each rate back-and-forth. Say `rate_words` verbatim.
    """
    try:
        result = compute_negotiation(
            loadboard_rate=loadboard_rate,
            our_offer=our_offer,
            carrier_counter=carrier_counter,
            round_num=round,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return NegotiationResponse(**result)
