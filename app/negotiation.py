"""Deterministic rate negotiation for voice agents."""

from app.number_words import dollars_to_words

DEFAULT_FLOOR_PCT = 0.92
MAX_ROUNDS = 3
ROUND2_PLUS_DEDUCTION = 30


def _round_dollars(amount: float) -> int:
    return int(round(amount))


def compute_negotiation(
    loadboard_rate: float,
    our_offer: float,
    carrier_counter: float,
    round_num: int,
    *,
    floor_pct: float = DEFAULT_FLOOR_PCT,
) -> dict:
    """
    Negotiation policy:
    - Round 1: split the difference with the carrier (from loadboard rate).
    - Round 2: last counter minus $30, clamp to floor.
    - Round 3: final offer = max(floor, last counter) — hold the line.
    - Round 3 + carrier still below floor → no_deal.
    """
    if round_num < 1 or round_num > MAX_ROUNDS:
        raise ValueError(f"round must be between 1 and {MAX_ROUNDS}")

    loadboard = _round_dollars(loadboard_rate)
    our = _round_dollars(our_offer)
    carrier = _round_dollars(carrier_counter)
    floor = _round_dollars(loadboard_rate * floor_pct)
    is_final = round_num >= MAX_ROUNDS

    if carrier >= floor and carrier <= our:
        return _accept(carrier)

    if round_num == 1:
        counter = _round_dollars((loadboard + carrier) / 2)
    elif round_num == 2:
        counter = our - ROUND2_PLUS_DEDUCTION
    else:
        counter = max(floor, our)

    counter = max(counter, floor)

    if is_final and carrier < floor:
        return {"action": "no_deal"}

    if counter >= carrier and carrier >= floor:
        return _accept(carrier)

    return _counter(counter)


def _counter(amount: int) -> dict:
    return {"action": "counter", "rate_words": dollars_to_words(amount)}


def _accept(amount: int) -> dict:
    return {"action": "accept", "rate_words": dollars_to_words(amount)}
