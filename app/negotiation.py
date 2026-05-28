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
    - Round 1: split the difference with the carrier (between our offer and theirs).
      If the split is below floor, counter at floor instead. Never accept outright.
    - Round 2: last counter minus $30, clamp to floor. Never accept outright.
    - Round 3: accept only if carrier is within [floor, our_offer]; otherwise hold
      at max(floor, our_offer) or no_deal if carrier is below floor.
    """
    if round_num < 1 or round_num > MAX_ROUNDS:
        raise ValueError(f"round must be between 1 and {MAX_ROUNDS}")

    our = _round_dollars(our_offer)
    carrier = _round_dollars(carrier_counter)
    floor = _round_dollars(loadboard_rate * floor_pct)

    if round_num == 1:
        counter = _round_dollars((our + carrier) / 2)
        counter = max(counter, floor)
        return _counter(counter)

    if round_num == 2:
        counter = max(our - ROUND2_PLUS_DEDUCTION, floor)
        return _counter(counter)

    # Round 3 — floor is the last-resort line; accept only here.
    if carrier < floor:
        return {"action": "no_deal"}

    if carrier <= our:
        return _accept(carrier)

    return _counter(max(floor, our))


def _counter(amount: int) -> dict:
    return {"action": "counter", "rate_words": dollars_to_words(amount)}


def _accept(amount: int) -> dict:
    return {"action": "accept", "rate_words": dollars_to_words(amount)}
