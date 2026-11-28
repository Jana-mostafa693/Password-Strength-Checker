"""SQLAlchemy model and a small database helper for anonymous statistics.

The `stats` table has NO password column. Only the environment name, the
strength label, a length bucket and a timestamp are stored.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import Column, DateTime, Integer, String, create_engine, func, select, text
from sqlalchemy.orm import Session, declarative_base

Base = declarative_base()


class Stat(Base):
    __tablename__ = "stats"

    id = Column(Integer, primary_key=True)
    env = Column(String(32), nullable=False)
    label = Column(String(16), nullable=False)
    length_bucket = Column(String(16), nullable=False)
    ts = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Database:
    """Lazy wrapper: the engine is created on first use, so importing the app
    never needs a reachable database."""

    def __init__(self, url) -> None:
        self._url = url
        self._engine = None

    @property
    def configured(self) -> bool:
        return self._url is not None

    @property
    def engine(self):
        if self._engine is None:
            kwargs = {"pool_pre_ping": True}
            if str(self._url).startswith("postgresql"):
                kwargs["connect_args"] = {"connect_timeout": 3}
            self._engine = create_engine(self._url, **kwargs)
        return self._engine

    def ping(self) -> bool:
        """True if a trivial query succeeds. Never raises."""
        if not self.configured:
            return False
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    def record(self, env: str, label: str, length_bucket: str) -> None:
        """Insert one anonymous statistics row. Raises on database errors."""
        with Session(self.engine) as session:
            session.add(Stat(env=env, label=label, length_bucket=length_bucket))
            session.commit()

    def count(self) -> int:
        with Session(self.engine) as session:
            return session.scalar(select(func.count()).select_from(Stat)) or 0

    def create_all(self) -> None:
        """Create tables from the model. Used by tests only; real deployments
        use db/init.sql."""
        Base.metadata.create_all(self.engine)
