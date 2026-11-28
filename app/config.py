"""Application configuration, read entirely from environment variables.

Nothing here is machine-specific: the same code runs on a VM, in Docker,
in Kubernetes and in the hybrid setup. Only the environment changes.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional

from sqlalchemy.engine import URL

DEFAULT_ENV_NAME = "local"
DEFAULT_DB_PORT = 5432
DEFAULT_DB_NAME = "passcheck"
DEFAULT_DB_USER = "passcheck"


@dataclass(frozen=True)
class Config:
    env_name: str = DEFAULT_ENV_NAME
    db_host: str = ""
    db_port: int = DEFAULT_DB_PORT
    db_name: str = DEFAULT_DB_NAME
    db_user: str = DEFAULT_DB_USER
    db_password: str = ""
    # Optional override (used by the automated tests with SQLite). Not part of
    # the Runbook's variable list and not needed in any deployment stage.
    database_url_override: str = ""

    @property
    def database_url(self) -> Optional[object]:
        """SQLAlchemy URL, or None when no database is configured."""
        if self.database_url_override:
            return self.database_url_override
        if not self.db_host:
            return None
        # URL.create() escapes special characters in the password safely.
        return URL.create(
            "postgresql+psycopg2",
            username=self.db_user,
            password=self.db_password or None,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        )

    @property
    def database_configured(self) -> bool:
        return self.database_url is not None

    @classmethod
    def from_env(cls, env: Mapping[str, str]) -> "Config":
        def get(name: str, default: str = "") -> str:
            value = (env.get(name) or "").strip()
            return value or default

        try:
            port = int(get("DB_PORT", str(DEFAULT_DB_PORT)))
        except ValueError:
            port = DEFAULT_DB_PORT
        return cls(
            env_name=get("ENV_NAME", DEFAULT_ENV_NAME),
            db_host=get("DB_HOST"),
            db_port=port,
            db_name=get("DB_NAME", DEFAULT_DB_NAME),
            db_user=get("DB_USER", DEFAULT_DB_USER),
            # Passwords are not stripped: whitespace could be significant.
            db_password=env.get("DB_PASSWORD") or "",
            database_url_override=get("DATABASE_URL"),
        )
