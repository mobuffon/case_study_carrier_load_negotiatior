from app.negotiation import compute_negotiation


def test_round1_meet_in_middle():
    r = compute_negotiation(1850, 1850, 2000, 1)
    assert r == {
        "action": "counter",
        "rate_words": "one thousand and nine hundred twenty-five dollars",
    }


def test_round2_last_offer_minus_thirty():
    r = compute_negotiation(1850, 1925, 2000, 2)
    assert r == {
        "action": "counter",
        "rate_words": "one thousand and eight hundred ninety-five dollars",
    }


def test_round3_holds_last_counter():
    r = compute_negotiation(1850, 1895, 2000, 3)
    assert r == {
        "action": "counter",
        "rate_words": "one thousand and eight hundred ninety-five dollars",
    }


def test_round1_splits_even_when_carrier_below_floor():
    # 1650 loadboard, carrier 1500, floor 1518 — split 1575 is above floor
    r = compute_negotiation(1650, 1650, 1500, 1)
    assert r == {
        "action": "counter",
        "rate_words": "one thousand and five hundred seventy-five dollars",
    }


def test_round1_clamps_to_floor_when_split_too_low():
    r = compute_negotiation(1850, 1850, 1400, 1)
    assert r["action"] == "counter"
    assert r["rate_words"] == "one thousand and seven hundred two dollars"


def test_round2_last_offer_minus_thirty_clamped_to_floor():
    r = compute_negotiation(1650, 1575, 1500, 2)
    assert r == {
        "action": "counter",
        "rate_words": "one thousand and five hundred forty-five dollars",
    }


def test_accept_when_carrier_at_or_below_offer():
    r = compute_negotiation(1850, 1850, 1800, 1)
    assert r == {
        "action": "accept",
        "rate_words": "one thousand and eight hundred dollars",
    }


def test_no_deal_when_carrier_below_floor_on_final_round():
    r = compute_negotiation(1650, 1545, 1500, 3)
    assert r == {"action": "no_deal"}


def test_negotiation_endpoint(client, auth_headers):
    r = client.get(
        "/negotiation/counter",
        params={
            "loadboard_rate": 1850,
            "our_offer": 1850,
            "carrier_counter": 2000,
            "round": 1,
        },
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json() == {
        "action": "counter",
        "rate_words": "one thousand and nine hundred twenty-five dollars",
    }


def test_negotiation_requires_auth(client):
    r = client.get(
        "/negotiation/counter",
        params={
            "loadboard_rate": 1850,
            "our_offer": 1850,
            "carrier_counter": 2000,
            "round": 1,
        },
    )
    assert r.status_code == 401


def test_invalid_round(client, auth_headers):
    r = client.get(
        "/negotiation/counter",
        params={
            "loadboard_rate": 1850,
            "our_offer": 1850,
            "carrier_counter": 2000,
            "round": 4,
        },
        headers=auth_headers,
    )
    assert r.status_code == 422
