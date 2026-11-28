import json


def post(client, payload, **kw):
    return client.post("/api/check", json=payload, **kw)


def test_check_returns_classification_and_never_echoes_password(client):
    secret = "Xq7!mPz2#Lw9vTr4"
    res = post(client, {"password": secret})
    assert res.status_code == 200
    body = res.get_json()
    assert body["label"] == "Very Strong" and body["score"] >= 80
    assert body["length_bucket"] == "16+" and body["recommendations"] == []
    assert body["recorded"] is False  # no database configured
    assert isinstance(body["checks"], list)
    assert secret not in res.get_data(as_text=True)
    assert res.headers["Cache-Control"] == "no-store"


def test_check_rejects_missing_empty_wrong_type_and_oversized_password(client):
    bad = [{}, {"pwd": "x"}, {"password": ""}, {"password": 12345}, {"password": None},
           {"password": ["a"]}, {"password": "a" * 129}, ["password"], "password"]
    for payload in bad:
        res = post(client, payload)
        assert res.status_code == 400, payload
        assert list(res.get_json()) == ["error"]


def test_check_rejects_invalid_json_and_oversized_body_safely(client):
    res = client.post("/api/check", data="{not json", content_type="application/json")
    assert res.status_code == 400 and "error" in res.get_json()
    res = client.post("/api/check", data="password=abc", content_type="text/plain")
    assert res.status_code == 400
    res = client.post("/api/check", data=json.dumps({"password": "a" * 10000}),
                      content_type="application/json")
    assert res.status_code == 413 and "error" in res.get_json()
    assert client.get("/api/check").status_code == 405


def test_health_reports_ok_with_host_identity(client):
    import socket
    res = client.get("/health")
    assert res.status_code == 200
    body = res.get_json()
    assert body["status"] == "ok" and body["host"] == socket.gethostname()


def test_ready_without_database_is_ready_for_local_development(client):
    res = client.get("/ready")
    assert res.status_code == 200
    assert res.get_json()["database"] == "not_configured"


def test_ready_returns_503_when_configured_database_is_unreachable(make_app, tmp_path):
    bad_url = f"sqlite:///{tmp_path / 'missing-dir' / 'x.db'}"
    res = make_app(DATABASE_URL=bad_url).test_client().get("/ready")
    assert res.status_code == 503
    body = res.get_json()
    assert body["status"] == "not_ready" and body["database"] == "unavailable"
    assert "missing-dir" not in res.get_data(as_text=True)  # no internal details leaked


def test_ready_ok_when_database_reachable(db_app):
    res = db_app.test_client().get("/ready")
    assert res.status_code == 200 and res.get_json()["database"] == "ok"
