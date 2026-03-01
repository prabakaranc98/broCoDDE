"""
BroCoDDE — Database Engine and Session Management

Data protection strategy:
- SQLite DB persists at backend/brocodde.db (never wiped on restart)
- Startup creates a dated backup before any migrations (max 7 kept)
- create_all() is additive only — never drops existing tables/data
- _sqlite_add_column_if_missing() handles new columns for existing DBs
"""

import shutil
from datetime import datetime
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


def _backup_db_on_startup():
    """Copy the SQLite DB to a dated backup before any startup migrations.
    Safe to call every restart — skips if a backup for today already exists.
    Keeps the last 7 daily backups.
    """
    if "sqlite" not in settings.database_url:
        return

    raw_path = settings.database_url.replace("sqlite+aiosqlite:///", "")
    db_path = Path(raw_path)
    if not db_path.exists():
        return  # Fresh install — nothing to back up yet

    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(exist_ok=True)

    today = datetime.utcnow().strftime("%Y%m%d")
    backup_path = backup_dir / f"brocodde.{today}.bak.db"

    if not backup_path.exists():
        shutil.copy2(db_path, backup_path)

    # Prune: keep last 7 daily backups
    all_backups = sorted(backup_dir.glob("brocodde.*.bak.db"))
    for old in all_backups[:-7]:
        old.unlink(missing_ok=True)


# Run backup at module import time (before engine connects)
_backup_db_on_startup()

engine = create_async_engine(
    settings.database_url,
    echo=False,  # SQL echo disabled — endpoint logs via logger.py middleware are sufficient
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def create_tables():
    """Create all tables on startup, and apply additive column migrations for SQLite.

    This is safe to run on every restart:
    - create_all() only creates missing tables, never drops or truncates existing ones.
    - _sqlite_add_column_if_missing() is a no-op if the column already exists.
    """
    from app.db import models  # noqa: F401 — register models

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        if "sqlite" in settings.database_url:
            # memory_entries migrations
            await _sqlite_add_column_if_missing(
                conn, "memory_entries", "source", "VARCHAR(20) NOT NULL DEFAULT 'user'"
            )
            await _sqlite_add_column_if_missing(
                conn, "memory_entries", "lifecycle_phases", "JSON NOT NULL DEFAULT '[]'"
            )
            # codde_tasks migrations
            await _sqlite_add_column_if_missing(
                conn, "codde_tasks", "chat_history", "JSON NOT NULL DEFAULT '[]'"
            )
            await _sqlite_add_column_if_missing(
                conn, "codde_tasks", "skeleton", "JSON"
            )
            await _sqlite_add_column_if_missing(
                conn, "codde_tasks", "lint_results", "JSON"
            )


async def _sqlite_add_column_if_missing(conn, table: str, column: str, definition: str):
    """Add a column to a SQLite table if it doesn't already exist."""
    from sqlalchemy import text
    result = await conn.execute(text(f"PRAGMA table_info({table})"))
    existing = [row[1] for row in result.fetchall()]
    if column not in existing:
        await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {definition}"))


async def get_db():
    """FastAPI dependency for database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
