from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from app import loads as loads_mod
from app.auth import require_api_key
from app.schemas import LoadOut, LoadSearchResponse

router = APIRouter(
    prefix="/loads",
    tags=["loads"],
    dependencies=[Depends(require_api_key)],
)


@router.get("/search", response_model=LoadSearchResponse)
def search(
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    equipment_type: Optional[str] = None,
    pickup_date: Optional[str] = None,
    limit: int = 5,
):
    results = loads_mod.search_loads(
        origin, destination, equipment_type, pickup_date, limit
    )
    return LoadSearchResponse(count=len(results), loads=[LoadOut(**r) for r in results])


@router.get("/{load_id}", response_model=LoadOut)
def get_one(load_id: str):
    load = loads_mod.get_load_by_id(load_id)
    if not load:
        raise HTTPException(status_code=404, detail=f"Load {load_id} not found")
    return LoadOut(**load)
