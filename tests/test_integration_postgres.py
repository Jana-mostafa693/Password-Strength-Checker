"""Integration tests against a REAL PostgreSQL database.

Skipped automatically unless DB_HOST is set. Requirements: the database exists
and db/init.sql has been applied. Run from the repository root:

    python -m pytest tests -q -v
"""
import os

import pytest
from sqlalchemy import text

from app import create_app

pytestmark = pytest.mark.skipif(not os.environ.get("DB_HOST"),
                                reason="DB_HOST not set: no PostgreSQL to test against")

SECRET = "Zz9$IntegrationSecret!77"


@pytest.fixture(scope="module")
def application():
    return create_app(dict(os.environ, ENV_NAME="docker"))


def test_ready_reports_database_ok(application):
    res = application.test_client().get("/ready")
    assert res.status_code == 200 and res.get_json()["database"] == "ok"


def test_check_inserts_one_anonymous_row(application):
    db = application.extensions["passcheck_db"]
    before = db.count()
    res = application.test_client().post("/api/check", json={"password": SECRET})
    assert res.status_code == 200 and res.get_json()["recorded"] is True
    assert db.count() == before + 1
    with db.engine.connect() as conn:
        row = conn.execute(text("SELECT env, label, length_bucket, ts FROM stats ORDER BY id DESC LIMIT 1")).one()
        dump = repr(conn.execute(text("SELECT * FROM stats")).fetchall())
        cols = {r[0] for r in conn.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'stats'"))}
    assert row.env == "docker" and row.length_bucket == "16+" and row.ts is not None
    assert cols == {"id", "env", "label", "length_bucket", "ts"}
    assert SECRET not in dump
