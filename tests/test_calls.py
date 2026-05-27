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


def test_create_call_happyrobot_empty_fields(client, auth_headers):
    payload = {
        "mc_number": "021708",
        "load_id": "L-1001",
        "loadboard_rate": 1850,
        "agreed_rate": "",
        "negotiation_rounds": "",
        "outcome": "Not interested",
        "sentiment": "neutral",
    }
    r = client.post("/calls", json=payload, headers=auth_headers)
    assert r.status_code == 201
    body = r.json()
    assert body["outcome"] == "declined"
    assert body["agreed_rate"] is None
    assert body["negotiation_rounds"] == 0


def test_seed_demo_calls(client, auth_headers):
    r = client.post("/calls/seed-demo?force=true", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["seeded"] == 15

    again = client.post("/calls/seed-demo", headers=auth_headers)
    assert again.json()["seeded"] == 0


def test_create_call_maps_success_outcome(client, auth_headers):
    payload = {
        "outcome": "Success",
        "sentiment": "positive",
        "agreed_rate": 1950,
        "loadboard_rate": 1850,
        "negotiation_rounds": 1,
    }
    r = client.post("/calls", json=payload, headers=auth_headers)
    assert r.status_code == 201
    assert r.json()["outcome"] == "booked"
