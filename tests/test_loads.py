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
    body = r.json()
    assert body["load_id"] == "L-1001"
    assert body["spoken"]["loadboard_rate"] == "one thousand and eight hundred fifty dollars"
    assert body["spoken"]["weight"] == "forty-two thousand pounds"
    assert body["spoken"]["load_id"] == "L dash one zero zero one"
