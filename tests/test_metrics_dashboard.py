def test_get_call_detail(client, auth_headers):
    create = client.post(
        "/calls",
        json={
            "mc_number": "021708",
            "load_id": "L-1001",
            "loadboard_rate": 1850,
            "agreed_rate": 1275,
            "negotiation_rounds": 2,
            "outcome": "booked",
            "sentiment": "neutral",
        },
        headers=auth_headers,
    )
    call_id = create.json()["id"]
    r = client.get(f"/calls/{call_id}", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["equipment_type"] == "Dry Van"
    assert body["commodity_type"] == "General Freight"
    assert body["origin"] == "Chicago IL"
    assert body["rate_delta"] == -575.0


def test_get_call_not_found(client, auth_headers):
    r = client.get("/calls/99999", headers=auth_headers)
    assert r.status_code == 404


def test_timeseries(client, auth_headers):
    r = client.get("/metrics/timeseries?window=24h", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["window"] == "24h"
    assert len(body["buckets"]) == 24

    r30 = client.get("/metrics/timeseries?window=30d", headers=auth_headers)
    assert r30.status_code == 200
    assert len(r30.json()["buckets"]) == 30


def test_volume_by_category(client, auth_headers):
    client.post(
        "/calls",
        json={
            "load_id": "L-1001",
            "outcome": "booked",
            "sentiment": "positive",
        },
        headers=auth_headers,
    )
    r = client.get("/metrics/volume?window=7d", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["equipment_type"]["Dry Van"] >= 1
    assert body["commodity_type"]["General Freight"] >= 1
    eq_total = sum(body["equipment_type"].values())
    cm_total = sum(body["commodity_type"].values())
    assert eq_total == cm_total
    assert eq_total >= 1
    assert sum(body["equipment_revenue"].values()) == sum(body["commodity_revenue"].values())
