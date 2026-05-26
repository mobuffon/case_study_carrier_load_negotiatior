def test_verify_mock_eligible(client, auth_headers):
    r = client.get("/carriers/verify?mc_number=12345", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["eligible"] is True


def test_verify_mock_ineligible(client, auth_headers):
    r = client.get("/carriers/verify?mc_number=99999", headers=auth_headers)
    assert r.json()["eligible"] is False
