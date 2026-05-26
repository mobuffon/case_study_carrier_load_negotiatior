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
