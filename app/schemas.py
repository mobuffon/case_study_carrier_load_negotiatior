from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel


OutcomeLiteral = Literal[
    "booked", "no_agreement", "not_eligible", "no_match", "declined", "abandoned", "error"
]
SentimentLiteral = Literal["positive", "neutral", "negative"]


class CarrierVerifyResponse(BaseModel):
    mc_number: str
    eligible: bool
    carrier_name: Optional[str] = None
    dot_number: Optional[str] = None
    status: Optional[str] = None
    reason: Optional[str] = None


class LoadOut(BaseModel):
    load_id: str
    origin: str
    destination: str
    pickup_datetime: str
    delivery_datetime: str
    equipment_type: str
    loadboard_rate: float
    notes: Optional[str] = None
    weight: Optional[float] = None
    commodity_type: Optional[str] = None
    num_of_pieces: Optional[int] = None
    miles: Optional[float] = None
    dimensions: Optional[str] = None


class LoadSearchResponse(BaseModel):
    count: int
    loads: list[LoadOut]


class CallCreate(BaseModel):
    mc_number: Optional[str] = None
    carrier_name: Optional[str] = None
    eligible: Optional[bool] = None
    load_id: Optional[str] = None
    loadboard_rate: Optional[float] = None
    agreed_rate: Optional[float] = None
    carrier_initial_offer: Optional[float] = None
    negotiation_rounds: int = 0
    outcome: OutcomeLiteral
    sentiment: SentimentLiteral
    notes: Optional[str] = None
    transcript_excerpt: Optional[str] = None
    duration_seconds: Optional[int] = None


class CallOut(BaseModel):
    id: int
    created_at: datetime
    mc_number: Optional[str]
    carrier_name: Optional[str]
    eligible: Optional[bool]
    load_id: Optional[str]
    loadboard_rate: Optional[float]
    agreed_rate: Optional[float]
    negotiation_rounds: int
    outcome: str
    sentiment: str
    notes: Optional[str]


class MetricsSummary(BaseModel):
    total_calls: int
    booked_count: int
    conversion_rate: float
    avg_negotiation_rounds: float
    avg_rate_delta_dollars: float
    avg_rate_delta_pct: float
    outcome_breakdown: dict[str, int]
    sentiment_breakdown: dict[str, int]
    eligibility_rate: float
