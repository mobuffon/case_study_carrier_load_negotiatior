from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.auth import require_api_key
from app.calls_helpers import build_timeseries, build_volume_breakdown
from app.db import get_session
from app.metrics_logic import compute_metrics_summary
from app.models import Call
from app.schemas import MetricsSummary, TimeSeriesResponse, VolumeMetricsResponse

router = APIRouter(
    prefix="/metrics",
    tags=["metrics"],
    dependencies=[Depends(require_api_key)],
)

_WINDOW_ALIASES = {"12h": "24h", "3h": "24h"}
_VALID_WINDOWS = frozenset({"24h", "7d", "30d"})


def _normalize_window(window: str) -> str:
    window = _WINDOW_ALIASES.get(window, window)
    if window not in _VALID_WINDOWS:
        raise HTTPException(
            status_code=422,
            detail="window must be one of: 24h, 7d, 30d",
        )
    return window


@router.get("/timeseries", response_model=TimeSeriesResponse)
def timeseries(
    window: str = Query("7d"),
    session: Session = Depends(get_session),
):
    window = _normalize_window(window)
    calls = session.exec(select(Call)).all()
    return TimeSeriesResponse(window=window, buckets=build_timeseries(calls, window))


@router.get("/volume", response_model=VolumeMetricsResponse)
def volume(
    window: str = Query("7d"),
    session: Session = Depends(get_session),
):
    window = _normalize_window(window)
    calls = session.exec(select(Call)).all()
    breakdown = build_volume_breakdown(calls, window)
    return VolumeMetricsResponse(
        window=window,
        equipment_type=breakdown["equipment_type"],
        commodity_type=breakdown["commodity_type"],
        equipment_revenue=breakdown["equipment_revenue"],
        commodity_revenue=breakdown["commodity_revenue"],
    )


@router.get("/summary", response_model=MetricsSummary)
def summary(session: Session = Depends(get_session)):
    calls = session.exec(select(Call)).all()
    return compute_metrics_summary(calls)
