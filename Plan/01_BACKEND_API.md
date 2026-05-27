# 01 — Backend API Spec

## Stack

- Python 3.11
- FastAPI (latest)
- SQLModel (latest) — wraps SQLAlchemy 2.x + Pydantic
- pydantic-settings — env-var-driven config
- httpx — async HTTP client for FMCSA calls
- uvicorn — ASGI server

`requirements.txt`:
```
fastapi==0.115.0
uvicorn[standard]==0.32.0
sqlmodel==0.0.22
pydantic==2.9.2
pydantic-settings==2.5.2
httpx==0.27.2
python-multipart==0.0.12
```

`requirements-dev.txt`:
```
pytest==8.3.3
pytest-asyncio==0.24.0
ruff==0.6.9
```

---

## File: `app/config.py`

Use `pydantic-settings` to load all env vars. Single `Settings` class, exposed as a `get_settings()` cached dependency.

```python
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    api_key: str
    fmcsa_webkey: str = ""
    database_url: str = "sqlite:///./app.db"
    log_level: str = "INFO"
    loads_csv_path: str = "app/data/loads.csv"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

---

## File: `app/auth.py`

A FastAPI dependency that validates the `X-API-Key` header. Use `Security(APIKeyHeader(...))` for OpenAPI docs.

```python
from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from app.config import get_settings, Settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(
    provided: str = Security(api_key_header),
    settings: Settings = Depends(get_settings),
) -> None:
    if not provided or provided != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
```

Apply via `dependencies=[Depends(require_api_key)]` on each protected route. Do NOT apply globally — `/health` and `/` (dashboard) must be public.

---

## File: `app/db.py`

SQLite engine and session management.

```python
from sqlmodel import SQLModel, create_engine, Session
from app.config import get_settings

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
        _engine = create_engine(settings.database_url, connect_args=connect_args, echo=False)
    return _engine


def init_db() -> None:
    SQLModel.metadata.create_all(get_engine())


def get_session():
    with Session(get_engine()) as session:
        yield session
```

`init_db()` is called once on FastAPI startup (lifespan event).

---

## File: `app/models.py`

Single ORM model for calls. Loads live in-memory only.

```python
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class Call(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    # Carrier identity
    mc_number: Optional[str] = Field(default=None, index=True)
    carrier_name: Optional[str] = None
    eligible: Optional[bool] = None

    # Load matched (nullable — no match scenarios)
    load_id: Optional[str] = Field(default=None, index=True)
    loadboard_rate_cents: Optional[int] = None
    agreed_rate_cents: Optional[int] = None

    # Negotiation
    negotiation_rounds: int = 0
    carrier_initial_offer_cents: Optional[int] = None

    # Classification (required on every call)
    outcome: str = Field(index=True)
    # one of: booked | no_agreement | not_eligible | no_match | declined | abandoned | error
    sentiment: str
    # one of: positive | neutral | negative

    # Optional context
    notes: Optional[str] = None
    transcript_excerpt: Optional[str] = None
    duration_seconds: Optional[int] = None
```

**Why cents**: avoids float drift on rate calculations. API responses convert back to dollars with 2 decimals.

---

## File: `app/schemas.py`

Pydantic request/response models. Keep ORM and API schemas separate.

```python
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator


# ===== Carrier verification =====
class CarrierVerifyResponse(BaseModel):
    mc_number: str
    eligible: bool
    carrier_name: Optional[str] = None
    dot_number: Optional[str] = None
    status: Optional[str] = None  # e.g. "ACTIVE", "INACTIVE"
    reason: Optional[str] = None  # explanation if not eligible


# ===== Loads =====
class LoadOut(BaseModel):
    load_id: str
    origin: str
    destination: str
    pickup_datetime: str           # ISO 8601 string
    delivery_datetime: str
    equipment_type: str
    loadboard_rate: float          # dollars
    notes: Optional[str] = None
    weight: Optional[float] = None
    commodity_type: Optional[str] = None
    num_of_pieces: Optional[int] = None
    miles: Optional[float] = None
    dimensions: Optional[str] = None


class LoadSearchResponse(BaseModel):
    count: int
    loads: list[LoadOut]


# ===== Calls =====
OutcomeLiteral = Literal[
    "booked", "no_agreement", "not_eligible", "no_match", "declined", "abandoned", "error"
]
SentimentLiteral = Literal["positive", "neutral", "negative"]


class CallCreate(BaseModel):
    mc_number: Optional[str] = None
    carrier_name: Optional[str] = None
    eligible: Optional[bool] = None
    load_id: Optional[str] = None
    loadboard_rate: Optional[float] = None       # dollars
    agreed_rate: Optional[float] = None          # dollars
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


# ===== Metrics =====
class MetricsSummary(BaseModel):
    total_calls: int
    booked_count: int
    conversion_rate: float                       # 0.0–1.0
    avg_negotiation_rounds: float
    avg_rate_delta_dollars: float                # agreed - loadboard, averaged over booked
    avg_rate_delta_pct: float                    # negative = discount, positive = premium
    outcome_breakdown: dict[str, int]
    sentiment_breakdown: dict[str, int]
    eligibility_rate: float                      # eligible / total verified
```

---

## File: `app/loads.py`

Load the CSV into memory at module import. Provide a `search()` function with simple filtering.

```python
import csv
from pathlib import Path
from typing import Optional
from app.config import get_settings


_loads_cache: list[dict] = []


def load_loads_from_csv() -> list[dict]:
    """Load and parse loads.csv. Called once at startup."""
    global _loads_cache
    path = Path(get_settings().loads_csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Loads CSV not found at {path}")

    loads = []
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["loadboard_rate"] = float(row["loadboard_rate"])
            row["weight"] = float(row["weight"]) if row.get("weight") else None
            row["num_of_pieces"] = int(row["num_of_pieces"]) if row.get("num_of_pieces") else None
            row["miles"] = float(row["miles"]) if row.get("miles") else None
            loads.append(row)
    _loads_cache = loads
    return loads


def get_all_loads() -> list[dict]:
    return _loads_cache


def get_load_by_id(load_id: str) -> Optional[dict]:
    for load in _loads_cache:
        if load["load_id"].lower() == load_id.lower():
            return load
    return None


def search_loads(
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    equipment_type: Optional[str] = None,
    pickup_date: Optional[str] = None,   # YYYY-MM-DD, matches the date portion
    limit: int = 5,
) -> list[dict]:
    """Case-insensitive substring match on origin/destination/equipment.
    Date match: any load whose pickup_datetime starts with the given date string."""
    results = []
    for load in _loads_cache:
        if origin and origin.lower() not in load["origin"].lower():
            continue
        if destination and destination.lower() not in load["destination"].lower():
            continue
        if equipment_type and equipment_type.lower() not in load["equipment_type"].lower():
            continue
        if pickup_date and not load["pickup_datetime"].startswith(pickup_date):
            continue
        results.append(load)
        if len(results) >= limit:
            break
    return results
```

Substring matching is intentional: HappyRobot users will say "Chicago" not "Chicago, IL", and the agent may pass either.

---

## File: `app/data/loads.csv`

Seed file with 15-20 realistic US loads. All 13 fields per the brief.

Columns (exact order):
```
load_id,origin,destination,pickup_datetime,delivery_datetime,equipment_type,loadboard_rate,notes,weight,commodity_type,num_of_pieces,miles,dimensions
```

Example rows (use realistic lanes — dates should be in the next 14 days from when you generate this; coding agent should use a date 7-14 days from today as a starting point and spread the loads across that window):

```
L-1001,Chicago IL,Dallas TX,2026-06-02T08:00:00,2026-06-03T18:00:00,Dry Van,1850.00,Drop and hook available,42000,General Freight,24,925,48ft x 8ft x 8.5ft
L-1002,Los Angeles CA,Phoenix AZ,2026-06-02T06:00:00,2026-06-02T20:00:00,Reefer,1400.00,Temp 34F required,38000,Produce,18,372,48ft x 8ft x 9ft
L-1003,Atlanta GA,Miami FL,2026-06-03T09:00:00,2026-06-04T14:00:00,Dry Van,1650.00,No touch freight,36000,Consumer Goods,20,662,53ft x 8ft x 9ft
L-1004,Seattle WA,Portland OR,2026-06-02T07:00:00,2026-06-02T15:00:00,Flatbed,950.00,Tarps required,45000,Lumber,12,174,48ft x 8ft x 8ft
L-1005,New York NY,Boston MA,2026-06-03T10:00:00,2026-06-03T18:00:00,Dry Van,800.00,Live unload,28000,Retail,30,215,53ft x 8ft x 9ft
L-1006,Houston TX,New Orleans LA,2026-06-04T08:00:00,2026-06-04T16:00:00,Reefer,1100.00,Temp 38F,40000,Seafood,15,348,48ft x 8ft x 9ft
L-1007,Denver CO,Salt Lake City UT,2026-06-05T07:00:00,2026-06-06T12:00:00,Dry Van,1250.00,Mountain pass route,32000,Electronics,22,525,53ft x 8ft x 9ft
L-1008,Charlotte NC,Nashville TN,2026-06-04T09:00:00,2026-06-04T20:00:00,Flatbed,1050.00,Oversize permit ready,46000,Steel,8,409,48ft x 8.5ft x 8ft
L-1009,Detroit MI,Cleveland OH,2026-06-03T08:00:00,2026-06-03T14:00:00,Dry Van,650.00,Quick turnaround,25000,Auto Parts,40,170,53ft x 8ft x 9ft
L-1010,Phoenix AZ,Las Vegas NV,2026-06-05T08:00:00,2026-06-05T16:00:00,Reefer,900.00,Temp 36F,35000,Beverages,28,297,48ft x 8ft x 9ft
L-1011,Memphis TN,St Louis MO,2026-06-06T07:00:00,2026-06-06T15:00:00,Dry Van,750.00,FCFS pickup,30000,Paper Products,35,284,53ft x 8ft x 9ft
L-1012,Kansas City MO,Oklahoma City OK,2026-06-04T10:00:00,2026-06-05T08:00:00,Dry Van,900.00,Drop trailer,33000,Packaging,26,343,53ft x 8ft x 9ft
L-1013,Minneapolis MN,Chicago IL,2026-06-05T06:00:00,2026-06-05T18:00:00,Reefer,1350.00,Temp 32F,41000,Dairy,20,408,48ft x 8ft x 9ft
L-1014,Portland OR,Sacramento CA,2026-06-06T08:00:00,2026-06-07T10:00:00,Flatbed,1450.00,Tarps required,44000,Building Materials,16,583,48ft x 8.5ft x 8ft
L-1015,Jacksonville FL,Atlanta GA,2026-06-07T09:00:00,2026-06-08T08:00:00,Dry Van,1100.00,Appointment required,34000,Furniture,18,346,53ft x 8ft x 9ft
```

Make sure the coding agent regenerates dates to be future-dated relative to when it builds the project.

---

## File: `app/fmcsa.py`

Wraps the FMCSA QCMobile API. Use the carrier-by-MC endpoint.

The relevant endpoint (verify against current FMCSA docs at build time):
```
GET https://mobile.fmcsa.dot.gov/qc/services/carriers/docket-number/{docket_number}?webKey={webKey}
```

Where docket_number is the MC number (without "MC-" prefix). The response is JSON with carrier details.

```python
import logging
from typing import Optional
import httpx
from app.config import get_settings
from app.schemas import CarrierVerifyResponse

logger = logging.getLogger(__name__)

FMCSA_BASE = "https://mobile.fmcsa.dot.gov/qc/services"


async def verify_carrier(mc_number: str) -> CarrierVerifyResponse:
    """Verify a carrier by MC number against FMCSA. Returns eligibility."""
    settings = get_settings()

    # Normalize: strip "MC-", "MC", spaces
    clean_mc = mc_number.upper().replace("MC-", "").replace("MC", "").strip()
    if not clean_mc.isdigit():
        return CarrierVerifyResponse(
            mc_number=mc_number, eligible=False,
            reason="Invalid MC number format"
        )

    if not settings.fmcsa_webkey:
        return _mock_response(clean_mc)

    url = f"{FMCSA_BASE}/carriers/docket-number/{clean_mc}"
    params = {"webKey": settings.fmcsa_webkey}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPError as e:
        logger.exception("FMCSA request failed")
        return CarrierVerifyResponse(
            mc_number=clean_mc, eligible=False,
            reason=f"FMCSA API error: {type(e).__name__}"
        )

    return _parse_fmcsa_response(clean_mc, data)


def _parse_fmcsa_response(mc: str, data: dict) -> CarrierVerifyResponse:
    """Parse FMCSA response. Structure varies — defensive parsing required."""
    content = data.get("content") if isinstance(data, dict) else None
    if not content:
        return CarrierVerifyResponse(
            mc_number=mc, eligible=False,
            reason="Carrier not found in FMCSA database"
        )

    # FMCSA returns content as a list of carrier records
    record = content[0] if isinstance(content, list) and content else content
    carrier = record.get("carrier", record) if isinstance(record, dict) else {}

    # Eligibility heuristic: allowed to operate AND not out of service
    allowed = carrier.get("allowedToOperate", "").upper() == "Y"
    oos = carrier.get("oosDate") not in (None, "", "null")
    status = "ACTIVE" if allowed and not oos else "INACTIVE"

    return CarrierVerifyResponse(
        mc_number=mc,
        eligible=allowed and not oos,
        carrier_name=carrier.get("legalName") or carrier.get("dbaName"),
        dot_number=str(carrier.get("dotNumber", "")),
        status=status,
        reason=None if (allowed and not oos) else "Carrier not authorized or out of service",
    )


def _mock_response(mc: str) -> CarrierVerifyResponse:
    """For local dev when FMCSA key is unavailable."""
    if mc.startswith("9"):
        return CarrierVerifyResponse(
            mc_number=mc, eligible=False,
            reason="Mock: not eligible (MC starts with 9)"
        )
    return CarrierVerifyResponse(
        mc_number=mc, eligible=True,
        carrier_name=f"Test Carrier {mc}",
        dot_number="1234567",
        status="ACTIVE",
    )
```

**Note for coding agent**: The FMCSA response schema has changed in the past. Build defensive parsing and log the raw response when fields are missing. Validate against the live API once the webkey is obtained.

---

## File: `app/routes/health.py`

Public, no auth.

```python
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}
```

---

## File: `app/routes/carriers.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from app.auth import require_api_key
from app.fmcsa import verify_carrier
from app.schemas import CarrierVerifyResponse

router = APIRouter(prefix="/carriers", tags=["carriers"], dependencies=[Depends(require_api_key)])


@router.get("/verify", response_model=CarrierVerifyResponse)
async def verify(mc_number: str):
    if not mc_number or not mc_number.strip():
        raise HTTPException(status_code=400, detail="mc_number is required")
    return await verify_carrier(mc_number)
```

---

## File: `app/routes/loads.py`

```python
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from app.auth import require_api_key
from app import loads as loads_mod
from app.schemas import LoadOut, LoadSearchResponse

router = APIRouter(prefix="/loads", tags=["loads"], dependencies=[Depends(require_api_key)])


@router.get("/search", response_model=LoadSearchResponse)
def search(
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    equipment_type: Optional[str] = None,
    pickup_date: Optional[str] = None,
    limit: int = 5,
):
    results = loads_mod.search_loads(origin, destination, equipment_type, pickup_date, limit)
    return LoadSearchResponse(count=len(results), loads=[LoadOut(**r) for r in results])


@router.get("/{load_id}", response_model=LoadOut)
def get_one(load_id: str):
    load = loads_mod.get_load_by_id(load_id)
    if not load:
        raise HTTPException(status_code=404, detail=f"Load {load_id} not found")
    return LoadOut(**load)
```

---

## File: `app/routes/calls.py`

```python
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select
from app.auth import require_api_key
from app.db import get_session
from app.models import Call
from app.schemas import CallCreate, CallOut

router = APIRouter(prefix="/calls", tags=["calls"], dependencies=[Depends(require_api_key)])


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
```

---

## File: `app/routes/metrics.py`

```python
from fastapi import APIRouter, Depends
from sqlmodel import Session, select, func
from app.auth import require_api_key
from app.db import get_session
from app.models import Call
from app.schemas import MetricsSummary

router = APIRouter(prefix="/metrics", tags=["metrics"], dependencies=[Depends(require_api_key)])


@router.get("/summary", response_model=MetricsSummary)
def summary(session: Session = Depends(get_session)):
    calls = session.exec(select(Call)).all()
    total = len(calls)

    if total == 0:
        return MetricsSummary(
            total_calls=0, booked_count=0, conversion_rate=0.0,
            avg_negotiation_rounds=0.0, avg_rate_delta_dollars=0.0,
            avg_rate_delta_pct=0.0, outcome_breakdown={}, sentiment_breakdown={},
            eligibility_rate=0.0,
        )

    booked = [c for c in calls if c.outcome == "booked"]
    booked_with_rates = [
        c for c in booked
        if c.agreed_rate_cents is not None and c.loadboard_rate_cents is not None
    ]

    avg_rounds = sum(c.negotiation_rounds for c in calls) / total

    if booked_with_rates:
        deltas_cents = [c.agreed_rate_cents - c.loadboard_rate_cents for c in booked_with_rates]
        avg_delta_cents = sum(deltas_cents) / len(deltas_cents)
        avg_delta_dollars = round(avg_delta_cents / 100, 2)
        avg_delta_pct = round(
            sum((c.agreed_rate_cents - c.loadboard_rate_cents) / c.loadboard_rate_cents
                for c in booked_with_rates) / len(booked_with_rates) * 100, 2
        )
    else:
        avg_delta_dollars = 0.0
        avg_delta_pct = 0.0

    outcome_breakdown: dict[str, int] = {}
    for c in calls:
        outcome_breakdown[c.outcome] = outcome_breakdown.get(c.outcome, 0) + 1

    sentiment_breakdown: dict[str, int] = {}
    for c in calls:
        sentiment_breakdown[c.sentiment] = sentiment_breakdown.get(c.sentiment, 0) + 1

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
        outcome_breakdown=outcome_breakdown,
        sentiment_breakdown=sentiment_breakdown,
        eligibility_rate=round(eligibility_rate, 4),
    )
```

---

## File: `app/main.py`

The FastAPI app entrypoint. Lifespan handles startup (init DB, load CSV).

```python
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.db import init_db
from app.loads import load_loads_from_csv
from app.routes import health, carriers, loads as loads_routes, calls, metrics


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logging.basicConfig(level=settings.log_level.upper())
    logging.getLogger(__name__).info("Starting up — initializing DB and loading loads CSV")
    init_db()
    load_loads_from_csv()
    yield
    logging.getLogger(__name__).info("Shutting down")


app = FastAPI(
    title="HappyRobot Carrier Sales API",
    version="0.1.0",
    lifespan=lifespan,
    description="Backend for inbound carrier load sales automation.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten in prod
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(health.router)
app.include_router(carriers.router)
app.include_router(loads_routes.router)
app.include_router(calls.router)
app.include_router(metrics.router)

# Dashboard static
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", include_in_schema=False)
def dashboard_root():
    return FileResponse(static_dir / "index.html")
```

---

## Testing (light — these are smoke tests, not exhaustive)

### `tests/conftest.py`

```python
import os
import pytest
from fastapi.testclient import TestClient

os.environ["API_KEY"] = "test-key-123"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["LOADS_CSV_PATH"] = "app/data/loads.csv"

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers():
    return {"X-API-Key": "test-key-123"}
```

### `tests/test_loads.py`

```python
def test_search_no_filters(client, auth_headers):
    r = client.get("/loads/search", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["count"] >= 1


def test_search_by_origin(client, auth_headers):
    r = client.get("/loads/search?origin=Chicago", headers=auth_headers)
    assert r.status_code == 200
    for load in r.json()["loads"]:
        assert "chicago" in load["origin"].lower()


def test_search_requires_auth(client):
    r = client.get("/loads/search")
    assert r.status_code == 401


def test_get_load_by_id(client, auth_headers):
    r = client.get("/loads/L-1001", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["load_id"] == "L-1001"
```

### `tests/test_carriers.py`

```python
def test_verify_mock_eligible(client, auth_headers):
    r = client.get("/carriers/verify?mc_number=12345", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["eligible"] is True


def test_verify_mock_ineligible(client, auth_headers):
    r = client.get("/carriers/verify?mc_number=99999", headers=auth_headers)
    assert r.json()["eligible"] is False
```

### `tests/test_calls.py`

```python
def test_create_call(client, auth_headers):
    payload = {
        "mc_number": "12345",
        "carrier_name": "Test Co",
        "eligible": True,
        "load_id": "L-1001",
        "loadboard_rate": 1850.00,
        "agreed_rate": 1900.00,
        "negotiation_rounds": 2,
        "outcome": "booked",
        "sentiment": "positive",
    }
    r = client.post("/calls", json=payload, headers=auth_headers)
    assert r.status_code == 201
    assert r.json()["agreed_rate"] == 1900.00


def test_metrics_after_call(client, auth_headers):
    r = client.get("/metrics/summary", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["total_calls"] >= 1
```

Run with `pytest`.

---

## Local Dev Commands

```bash
# Setup
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

# Generate an API key
python -c "import secrets; print(secrets.token_hex(16))"

# Copy env and set values
cp .env.example .env
# edit .env

# Run
uvicorn app.main:app --reload --port 8000

# Visit OpenAPI docs
open http://localhost:8000/docs
```
