import sqlite3

from app import db
from app.config import settings
from app.db import get_conn


def test_init_db_dedupes_legacy_ticket_links(tmp_path):
    """A database created before idx_ticket_links_unique_pair can hold mirrored
    duplicate links. init_db() must dedupe them and then create the unique index
    instead of crashing on startup."""
    db_path = tmp_path / "legacy.db"
    object.__setattr__(settings, "database_path", str(db_path))

    legacy = sqlite3.connect(str(db_path))
    legacy.executescript(
        """
        CREATE TABLE ticket_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            source_ticket_id INTEGER NOT NULL,
            target_ticket_id INTEGER NOT NULL,
            link_type TEXT NOT NULL DEFAULT 'relates',
            created_by INTEGER,
            created_at TEXT NOT NULL
        );
        INSERT INTO ticket_links
            (project_id, source_ticket_id, target_ticket_id, link_type, created_at)
            VALUES (1, 10, 20, 'relates', 't');
        INSERT INTO ticket_links
            (project_id, source_ticket_id, target_ticket_id, link_type, created_at)
            VALUES (1, 20, 10, 'blocks', 't');
        """
    )
    legacy.commit()
    legacy.close()

    db.init_db()  # must not raise

    with get_conn() as conn:
        remaining = conn.execute("SELECT COUNT(*) FROM ticket_links").fetchone()[0]
        index_present = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master "
            "WHERE type = 'index' AND name = 'idx_ticket_links_unique_pair'"
        ).fetchone()[0]
    assert remaining == 1
    assert index_present == 1


def test_connection_sets_busy_timeout(temp_db):
    # Without a busy_timeout, a brief writer overlap surfaces as a
    # "database is locked" error instead of waiting. Connections must opt in.
    with get_conn() as conn:
        assert conn.execute("PRAGMA busy_timeout").fetchone()[0] == 5000


def test_connection_enforces_foreign_keys(temp_db):
    with get_conn() as conn:
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
