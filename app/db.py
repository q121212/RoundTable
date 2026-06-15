import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, List, Optional

from .config import settings


TICKET_STATUSES = ["Backlog", "Todo", "In Progress", "Review", "Done", "Closed"]
PRIORITIES = ["Low", "Medium", "High", "Urgent"]
TICKET_TYPES = ["Task", "Epic", "Bug", "Story"]
TICKET_LINK_TYPES = ["relates", "blocks", "blocked_by", "duplicates", "parent"]


def utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def row_to_dict(row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
    if row is None:
        return None
    return {key: row[key] for key in row.keys()}


def rows_to_dicts(rows: List[sqlite3.Row]) -> List[Dict[str, Any]]:
    return [row_to_dict(row) or {} for row in rows]


def connect() -> sqlite3.Connection:
    db_dir = os.path.dirname(settings.database_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(settings.database_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                github_id TEXT UNIQUE,
                login TEXT NOT NULL UNIQUE,
                name TEXT,
                email TEXT,
                avatar_url TEXT,
                role TEXT NOT NULL DEFAULT 'member',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                token_hash TEXT NOT NULL UNIQUE,
                csrf_token TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                next_ticket_number INTEGER NOT NULL DEFAULT 1,
                github_repo_full_name TEXT,
                github_installation_id TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS project_members (
                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                role TEXT NOT NULL DEFAULT 'member',
                created_at TEXT NOT NULL,
                PRIMARY KEY (project_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                number INTEGER NOT NULL,
                key TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                ticket_type TEXT NOT NULL DEFAULT 'Task',
                status TEXT NOT NULL DEFAULT 'Backlog',
                priority TEXT NOT NULL DEFAULT 'Medium',
                assignee_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                reporter_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                closed_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE (project_id, number)
            );

            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                body TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS watchers (
                ticket_id INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                created_at TEXT NOT NULL,
                PRIMARY KEY (ticket_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS ticket_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                source_ticket_id INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
                target_ticket_id INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
                link_type TEXT NOT NULL DEFAULT 'relates',
                created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                created_at TEXT NOT NULL,
                UNIQUE (source_ticket_id, target_ticket_id, link_type),
                CHECK (source_ticket_id != target_ticket_id)
            );

            CREATE TABLE IF NOT EXISTS action_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
                ticket_id INTEGER REFERENCES tickets(id) ON DELETE CASCADE,
                actor_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                action TEXT NOT NULL,
                field TEXT,
                old_value TEXT,
                new_value TEXT,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS github_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
                repo_full_name TEXT NOT NULL,
                ref_type TEXT NOT NULL,
                ref_name TEXT NOT NULL,
                url TEXT,
                sha TEXT,
                title TEXT,
                state TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE (ticket_id, repo_full_name, ref_type, ref_name)
            );

            CREATE TABLE IF NOT EXISTS github_deliveries (
                delivery_id TEXT PRIMARY KEY,
                event TEXT NOT NULL,
                received_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS mcp_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                token_hash TEXT NOT NULL UNIQUE,
                prefix TEXT NOT NULL,
                last_used_at TEXT,
                revoked_at TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS notification_preferences (
                user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                email_enabled INTEGER NOT NULL DEFAULT 1,
                telegram_enabled INTEGER NOT NULL DEFAULT 1,
                muted_projects_json TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS telegram_links (
                user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                chat_id TEXT NOT NULL,
                username TEXT,
                linked_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS telegram_link_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                token_hash TEXT NOT NULL UNIQUE,
                expires_at TEXT NOT NULL,
                used_at TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS notification_outbox (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                channel TEXT NOT NULL,
                event_type TEXT NOT NULL,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                attempts INTEGER NOT NULL DEFAULT 0,
                next_attempt_at TEXT NOT NULL,
                last_error TEXT,
                dedupe_key TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL,
                sent_at TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_tickets_project_status
                ON tickets(project_id, status, updated_at);
            CREATE INDEX IF NOT EXISTS idx_action_log_ticket
                ON action_log(ticket_id, created_at);
            CREATE INDEX IF NOT EXISTS idx_ticket_links_source
                ON ticket_links(source_ticket_id, created_at);
            CREATE INDEX IF NOT EXISTS idx_ticket_links_target
                ON ticket_links(target_ticket_id, created_at);
            CREATE INDEX IF NOT EXISTS idx_notification_outbox_due
                ON notification_outbox(status, next_attempt_at);
            """
        )
        # Additive, idempotent column migrations for existing databases.
        _add_column_if_missing(conn, "mcp_tokens", "suffix", "TEXT")
        _add_column_if_missing(conn, "projects", "statuses_json", "TEXT")
        _add_column_if_missing(conn, "projects", "ticket_types_json", "TEXT")
        _add_column_if_missing(conn, "tickets", "ticket_type", "TEXT NOT NULL DEFAULT 'Task'")


def _add_column_if_missing(conn: sqlite3.Connection, table: str, column: str, decl: str) -> None:
    existing = [row["name"] for row in conn.execute("PRAGMA table_info(%s)" % table)]
    if column not in existing:
        conn.execute("ALTER TABLE %s ADD COLUMN %s %s" % (table, column, decl))


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def json_loads(value: Optional[str], default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default
