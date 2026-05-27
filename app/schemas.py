from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, field_validator, model_validator

from app.number_words import build_load_spoken

OutcomeLiteral = Literal[
    "booked", "no_agreement", "not_eligible", "no_match", "declined", "abandoned", "error"
]
SentimentLiteral = Literal["positive", "neutral", "negative"]

_OUTCOME_ALIASES = {
    "success": "booked",
    "sucess": "booked",
    "booked": "booked",
    "rate too high": "no_agreement",
    "no agreement": "no_agreement",
    "not interested": "declined",
    "declined": "declined",
    "not eligible": "not_eligible",
    "no match": "no_match",
    "abandoned": "abandoned",
    "error": "error",
}


class LoadSpoken(BaseModel):
    load_id: str
    loadboard_rate: str
    weight: Optional[str] = None
    num_of_pieces: Optional[str] = None
    miles: Optional[str] = None


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
    spoken: Optional[LoadSpoken] = None

    @model_validator(mode="after")
    def populate_spoken(self) -> "LoadOut":
        self.spoken = LoadSpoken(
            **build_load_spoken(
                load_id=self.load_id,
                loadboard_rate=self.loadboard_rate,
                weight=self.weight,
                num_of_pieces=self.num_of_pieces,
                miles=self.miles,
            )
        )
        return self


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
    negotiation_rounds: int = 0
    outcome: OutcomeLiteral
    sentiment: SentimentLiteral
    notes: Optional[str] = None
    transcript_excerpt: Optional[str] = None
    duration_seconds: Optional[int] = None

    @field_validator("loadboard_rate", "agreed_rate", mode="before")
    @classmethod
    def empty_str_to_none_float(cls, v):
        if v == "" or v == "null" or v is None:
            return None
        return v

    @field_validator("negotiation_rounds", mode="before")
    @classmethod
    def empty_int_to_zero(cls, v):
        if v == "" or v is None:
            return 0
        return v

    @field_validator("duration_seconds", mode="before")
    @classmethod
    def empty_str_to_none_int(cls, v):
        if v == "" or v == "null" or v is None:
            return None
        return v

    @field_validator("mc_number", "load_id", "notes", "transcript_excerpt", mode="before")
    @classmethod
    def empty_str_to_none_str(cls, v):
        if v == "" or v == "null":
            return None
        return v

    @field_validator("outcome", mode="before")
    @classmethod
    def map_outcome(cls, v):
        if not isinstance(v, str):
            return v
        normalized = v.strip().lower()
        return _OUTCOME_ALIASES.get(normalized, v)


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
    origin: Optional[str] = None
    destination: Optional[str] = None
    equipment_type: Optional[str] = None
    commodity_type: Optional[str] = None
    duration_seconds: Optional[int] = None


class CallDetailOut(CallOut):
    rate_delta: Optional[float] = None
    rate_delta_pct: Optional[float] = None
    pickup_datetime: Optional[str] = None
    delivery_datetime: Optional[str] = None
    weight: Optional[float] = None
    miles: Optional[float] = None
    num_of_pieces: Optional[int] = None
    dimensions: Optional[str] = None
    load_notes: Optional[str] = None
    transcript_excerpt: Optional[str] = None
    transcript_messages: list[dict] = []


class TimeSeriesBucket(BaseModel):
    label: str
    start: str
    end: str
    total: int
    booked: int


class TimeSeriesResponse(BaseModel):
    window: str
    buckets: list[TimeSeriesBucket]


class VolumeMetricsResponse(BaseModel):
    window: str
    equipment_type: dict[str, int]
    commodity_type: dict[str, int]
    equipment_revenue: dict[str, float]
    commodity_revenue: dict[str, float]


class MetricsSummary(BaseModel):
    total_calls: int
    booked_count: int
    conversion_rate: float
    avg_negotiation_rounds: float
    avg_rate_delta_dollars: float
    avg_rate_delta_pct: float
    avg_listed_rate: float
    avg_agreed_rate: float
    negotiation_efficiency: float
    outcome_breakdown: dict[str, int]
    sentiment_breakdown: dict[str, int]
    decline_reason_breakdown: dict[str, int]
    eligibility_rate: float


class NegotiationResponse(BaseModel):
    action: Literal["counter", "accept", "no_deal"]
    rate_words: Optional[str] = None
