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
            row["num_of_pieces"] = (
                int(row["num_of_pieces"]) if row.get("num_of_pieces") else None
            )
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
    pickup_date: Optional[str] = None,
    limit: int = 5,
) -> list[dict]:
    """Case-insensitive substring match on origin/destination/equipment."""
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
