import os
import sys

import pytest

# Make `import app`, `import scoring` ... work when pytest runs from app/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402


@pytest.fixture
def make_app():
    """Build an app from an explicit environment dict (ignores the real env)."""
    def _make(**env):
        return create_app({k: v for k, v in env.items()})
    return _make


@pytest.fixture
def client(make_app):
    """App with NO database, like local development."""
    return make_app(ENV_NAME="docker").test_client()


@pytest.fixture
def db_app(make_app, tmp_path):
    """App backed by a throw-away SQLite file with the stats table created."""
    url = f"sqlite:///{tmp_path / 'stats.db'}"
    application = make_app(ENV_NAME="kubernetes", DATABASE_URL=url)
    application.extensions["passcheck_db"].create_all()
    return application
