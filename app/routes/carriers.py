from fastapi import APIRouter, Depends, HTTPException

from app.auth import require_api_key
from app.fmcsa import verify_carrier
from app.schemas import CarrierVerifyResponse

router = APIRouter(
    prefix="/carriers",
    tags=["carriers"],
    dependencies=[Depends(require_api_key)],
)


@router.get("/verify", response_model=CarrierVerifyResponse)
async def verify(mc_number: str):
    if not mc_number or not mc_number.strip():
        raise HTTPException(status_code=400, detail="mc_number is required")
    return await verify_carrier(mc_number)
