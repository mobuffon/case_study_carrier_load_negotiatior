from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Call(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    mc_number: Optional[str] = Field(default=None, index=True)
    carrier_name: Optional[str] = None
    eligible: Optional[bool] = None

    load_id: Optional[str] = Field(default=None, index=True)
    loadboard_rate_cents: Optional[int] = None
    agreed_rate_cents: Optional[int] = None

    negotiation_rounds: int = 0
    carrier_initial_offer_cents: Optional[int] = None

    outcome: str = Field(index=True)
    sentiment: str

    notes: Optional[str] = None
    transcript_excerpt: Optional[str] = None
    duration_seconds: Optional[int] = None
