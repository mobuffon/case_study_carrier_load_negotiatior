import json
from datetime import datetime, timedelta
from typing import Optional

from app import loads as loads_mod
from app.models import Call

WINDOW_DELTAS = {
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}


def _cents_to_dollars(c: Optional[int]) -> Optional[float]:
    return round(c / 100, 2) if c is not None else None


def get_load_for_call(call: Call) -> Optional[dict]:
    if not call.load_id:
        return None
    return loads_mod.get_load_by_id(call.load_id)


def enrich_call(call: Call, include_transcript: bool = False) -> dict:
    load = get_load_for_call(call)
    loadboard_rate = _cents_to_dollars(call.loadboard_rate_cents)
    agreed_rate = _cents_to_dollars(call.agreed_rate_cents)
    rate_delta = None
    rate_delta_pct = None
    if loadboard_rate is not None and agreed_rate is not None:
        rate_delta = round(agreed_rate - loadboard_rate, 2)
        if loadboard_rate:
            rate_delta_pct = round((rate_delta / loadboard_rate) * 100, 2)

    data = {
        "id": call.id,
        "created_at": call.created_at,
        "mc_number": call.mc_number,
        "carrier_name": call.carrier_name,
        "eligible": call.eligible,
        "load_id": call.load_id,
        "loadboard_rate": loadboard_rate,
        "agreed_rate": agreed_rate,
        "rate_delta": rate_delta,
        "rate_delta_pct": rate_delta_pct,
        "negotiation_rounds": call.negotiation_rounds,
        "outcome": call.outcome,
        "sentiment": call.sentiment,
        "notes": call.notes,
        "duration_seconds": call.duration_seconds,
        "origin": load.get("origin") if load else None,
        "destination": load.get("destination") if load else None,
        "equipment_type": load.get("equipment_type") if load else None,
        "commodity_type": load.get("commodity_type") if load else None,
        "pickup_datetime": load.get("pickup_datetime") if load else None,
        "delivery_datetime": load.get("delivery_datetime") if load else None,
        "weight": load.get("weight") if load else None,
        "miles": load.get("miles") if load else None,
        "num_of_pieces": load.get("num_of_pieces") if load else None,
        "dimensions": load.get("dimensions") if load else None,
        "load_notes": load.get("notes") if load else None,
    }

    if include_transcript:
        data["transcript_excerpt"] = call.transcript_excerpt
        data["transcript_messages"] = parse_transcript(call.transcript_excerpt)

    return data


def parse_transcript(raw: Optional[str]) -> list[dict]:
    if not raw or raw.strip() in ("", "[]"):
        return []
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return parsed
    except json.JSONDecodeError:
        pass
    return [{"role": "text", "content": raw}]


def filter_calls_since(calls: list[Call], since: datetime) -> list[Call]:
    return [c for c in calls if c.created_at >= since]


def build_timeseries(calls: list[Call], window: str) -> list[dict]:
    delta = WINDOW_DELTAS[window]
    now = datetime.utcnow()
    since = now - delta
    filtered = filter_calls_since(calls, since)

    if window == "24h":
        bucket_size = timedelta(hours=1)
        bucket_count = 24
    elif window == "7d":
        bucket_size = timedelta(days=1)
        bucket_count = 7
    else:
        bucket_size = timedelta(days=1)
        bucket_count = 30

    buckets = []
    for i in range(bucket_count):
        start = since + bucket_size * i
        end = since + bucket_size * (i + 1)
        in_bucket = [c for c in filtered if start <= c.created_at < end]
        booked = sum(1 for c in in_bucket if c.outcome == "booked")
        buckets.append(
            {
                "label": _bucket_label(start, window),
                "start": start.isoformat(),
                "end": end.isoformat(),
                "total": len(in_bucket),
                "booked": booked,
            }
        )
    return buckets


def build_volume_breakdown(calls: list[Call], window: str) -> dict:
    delta = WINDOW_DELTAS[window]
    since = datetime.utcnow() - delta
    filtered = filter_calls_since(calls, since)

    equipment: dict[str, int] = {}
    commodity: dict[str, int] = {}
    equipment_revenue: dict[str, float] = {}
    commodity_revenue: dict[str, float] = {}

    for call in filtered:
        load = get_load_for_call(call)
        if not load:
            continue

        eq = (load.get("equipment_type") or "").strip() or "Unknown"
        cm = (load.get("commodity_type") or "").strip() or "Unknown"
        equipment[eq] = equipment.get(eq, 0) + 1
        commodity[cm] = commodity.get(cm, 0) + 1

        if call.outcome == "booked" and call.agreed_rate_cents is not None:
            rev = call.agreed_rate_cents / 100
            equipment_revenue[eq] = equipment_revenue.get(eq, 0.0) + rev
            commodity_revenue[cm] = commodity_revenue.get(cm, 0.0) + rev

    return {
        "equipment_type": equipment,
        "commodity_type": commodity,
        "equipment_revenue": {k: round(v, 2) for k, v in equipment_revenue.items()},
        "commodity_revenue": {k: round(v, 2) for k, v in commodity_revenue.items()},
    }


def decline_reason_from_call(call: Call) -> str:
    if call.notes:
        note = call.notes.strip().lower()
        if "rate" in note or "price" in note or "high" in note:
            return "rate too high"
        if "timing" in note or "time" in note:
            return "timing"
        if "equipment" in note:
            return "equipment mismatch"
        if "not interested" in note:
            return "not interested"
        return call.notes.strip()[:40]
    if call.outcome == "declined":
        return "not interested"
    if call.outcome == "no_agreement":
        return "rate too high"
    return "other"


def _bucket_label(start: datetime, window: str) -> str:
    if window == "24h":
        return start.strftime("%H:%M")
    if window == "30d":
        return start.strftime("%b %d")
    return start.strftime("%a %b %d")
