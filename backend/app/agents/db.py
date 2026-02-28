"""
BroCoDDE — Agno Database and Memory Setup
Shared SqliteDb instance used by all agents for native memory and session storage.
"""

from pathlib import Path

from agno.db.sqlite import SqliteDb

# Single shared DB for all agents — enables cross-agent memory sharing (Agno pattern)
DB_PATH = Path(__file__).parent.parent.parent / "brocodde.db"
agno_db = SqliteDb(db_file=str(DB_PATH))
