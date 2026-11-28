import logging
import sqlite3

from sqlalchemy import inspect

from config import Config

SECRET = "Zz9$SuperSecretPw!42"


def test_environment_configuration_and_footer(make_app):
    cfg = Config.from_env({"ENV_NAME": "hybrid", "DB_HOST": "vm-db", "DB_PORT": "5432",
                           "DB_NAME": "passcheck", "DB_USER": "passcheck",
                           "DB_PASSWORD": "p@ss:w/rd#1"})
    url = cfg.database_url
    assert cfg.env_name == "hybrid" and url.host == "vm-db" and url.port == 5432
    assert url.database == "passcheck" and url.username == "passcheck"
    assert url.password == "p@ss:w/rd#1"  # special characters survive intact
    # defaults: no database, local environment, bad port falls back to 5432
    empty = Config.from_env({})
    assert empty.env_name == "local" and empty.database_url is None and not empty.database_configured
    assert Config.from_env({"DB_HOST": "db", "DB_PORT": "abc"}).db_port == 5432
    # the footer shows the configured environment
    for name in ("vm", "docker", "kubernetes", "hybrid"):
        html = make_app(ENV_NAME=name).test_client().get("/").get_data(as_text=True)
        assert "Environment: <strong id=\"env-name\">" + name + "</strong>" in html


def test_statistics_are_recorded_anonymously_and_survive_instance_replacement(db_app, make_app):
    client = db_app.test_client()
    for pw in ("abc", "Hello#Pass9", "Xq7!mPz2#Lw9vTr4"):
        res = client.post("/api/check", json={"password": pw})
        assert res.status_code == 200 and res.get_json()["recorded"] is True
    db = db_app.extensions["passcheck_db"]
    columns = {c["name"] for c in inspect(db.engine).get_columns("stats")}
    assert columns == {"id", "env", "label", "length_bucket", "ts"}  # no password column
    with db.engine.connect() as conn:
        rows = conn.exec_driver_sql("SELECT env, label, length_bucket, ts FROM stats ORDER BY id").fetchall()
    assert [(r[0], r[1], r[2]) for r in rows] == [
        ("kubernetes", "Weak", "1-7"), ("kubernetes", "Strong", "8-11"),
        ("kubernetes", "Very Strong", "16+")]
    assert all(r[3] is not None for r in rows)
    # a "replacement pod": brand-new app instance, same database, data is still there
    replacement = make_app(ENV_NAME="kubernetes", DATABASE_URL=str(db.engine.url))
    assert replacement.extensions["passcheck_db"].count() == 3


def test_password_is_never_logged_printed_stored_or_leaked(make_app, db_app, tmp_path, caplog, capsys):
    caplog.set_level(logging.DEBUG)
    # 1. normal request with a working database
    ok = db_app.test_client().post("/api/check", json={"password": SECRET})
    assert ok.status_code == 200
    # 2. database failure while recording: request must still succeed
    broken = make_app(DATABASE_URL=f"sqlite:///{tmp_path / 'nope' / 'x.db'}").test_client()
    res = broken.post("/api/check", json={"password": SECRET})
    assert res.status_code == 200 and res.get_json()["recorded"] is False
    # 3. malformed request that contains the secret
    bad = broken.post("/api/check", data='{"password": "' + SECRET + '"', content_type="application/json")
    assert bad.status_code == 400
    # nothing leaked into responses, logs or the terminal
    for response in (ok, res, bad):
        assert SECRET not in response.get_data(as_text=True)
        assert SECRET not in str(response.headers)
    out = capsys.readouterr()
    assert SECRET not in caplog.text and SECRET not in out.out and SECRET not in out.err
    # and nothing in the database file (raw bytes) or any row
    db_file = str(db_app.extensions["passcheck_db"].engine.url.database)
    with open(db_file, "rb") as fh:
        assert SECRET.encode() not in fh.read()
    with sqlite3.connect(db_file) as conn:
        dump = repr(conn.execute("SELECT * FROM stats").fetchall())
    assert SECRET not in dump
