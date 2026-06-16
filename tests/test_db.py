from app.db import get_conn


def test_connection_sets_busy_timeout(temp_db):
    # Without a busy_timeout, a brief writer overlap surfaces as a
    # "database is locked" error instead of waiting. Connections must opt in.
    with get_conn() as conn:
        assert conn.execute("PRAGMA busy_timeout").fetchone()[0] == 5000


def test_connection_enforces_foreign_keys(temp_db):
    with get_conn() as conn:
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
