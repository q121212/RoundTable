# Architecture

RoundTable is a single-process FastAPI app with server-rendered Jinja templates,
vanilla JS, and SQLite. This document describes the layers and the allowed
dependency directions between them. The rules here are enforced by
`tests/test_architecture_boundaries.py`; if you change the structure, update both.

## Layers and responsibilities

| Layer | File(s) | Responsibility | Must NOT contain |
|-------|---------|----------------|------------------|
| HTTP / routes | `app/main.py` | Routes, request/form parsing, CSRF calls, redirects, template rendering, SSE route wiring | Complex business logic, SQL, deep domain processing |
| Data + domain | `app/store/` | Data access, domain operations, authorization boundaries | — |
| Store facade | `app/store/__init__.py` | **Only** re-exports of submodule public names + the dependency-DAG docstring | Function/class bodies, business logic, SQL |
| Schema / DB | `app/db.py` | Schema, connections, SQLite PRAGMAs, additive idempotent migrations | Business logic, route or domain rules |
| Security | `app/security.py` | Sessions, CSRF, hashing, HMAC, safe security helpers | Route-specific business rules |
| Notifications worker | `app/notifications.py` | Async outbox worker / orchestration. Blocking I/O (SMTP) only via `asyncio.to_thread` | Synchronous blocking calls on the event loop |
| Frontend / i18n | `app/static/app.js`, `app/templates/` | UI, board interactions, i18n. User-visible labels go through i18n keys | Hardcoded English labels for UI that can be RU; backend business rules that bypass server validation |
| Deploy / ops | `deploy.sh`, `deploy/`, `docs/` | Deploy-only logic: rsync, backup, dry-run, healthcheck | Changing server infra (Caddy/HAProxy/firewall/systemd) from app code |

### `app/store/` submodules

The store is a package whose `__init__.py` is a pure facade. Each submodule owns
one slice of the domain:

| Module | Responsibility |
|--------|----------------|
| `_validation.py` | Validators / normalizers / per-project config helpers |
| `_policies.py` | Access policies / authorization (`require_project_*`, `can_*`) |
| `_read_models.py` | Shared **read-only** ticket SELECTs and row mapping |
| `_action_log.py` | Action-log writes (and notify fan-out trigger) |
| `_notification_outbox.py` | Notification outbox, recipients, preferences |
| `_users.py` | User records, global-admin role sync |
| `_projects.py` | Project CRUD, members, settings |
| `_sprints.py` | Sprint operations |
| `_tickets.py` | Ticket mutations, comments, links, search, sort order |
| `_board.py` | Board read model |
| `_statistics.py` | Project statistics |
| `_integrations.py` | GitHub integration state/helpers |
| `_accounts.py` | MCP tokens, Telegram links, API audit, retention, test notification |

## Dependency rules

Allowed direction is **downward only**. The store submodules form a strict
acyclic DAG:

```
_validation          (leaf)
_read_models         (leaf)
_policies            -> _validation
_notification_outbox -> _read_models
_action_log          -> _notification_outbox
_users               -> _notification_outbox
_projects            -> _validation, _policies, _action_log, _notification_outbox
_sprints             -> _projects, _policies, _action_log, _validation
_integrations        -> _validation, _read_models, _action_log
_accounts            -> _notification_outbox
_tickets             -> _projects, _sprints, _read_models, _policies, _validation, _action_log
_board               -> _projects, _sprints, _read_models, _policies, _validation
_statistics          -> _projects, _sprints, _policies, _validation
```

Hard rules (enforced by tests):

- `app/store/` submodules **must never** import `app.main`.
- Store submodules **must not** import the `app.store` facade
  (`app/store/__init__.py`). The facade imports submodules; never the reverse.
- `app/store/__init__.py` is facade-only: imports/re-exports and a docstring,
  **no** function or class definitions.
- `_read_models.py` must stay read-only: it must **not** import `_tickets`,
  `_projects`, `_action_log`, or `_notification_outbox`. (This is the seam that
  keeps the notifications↔tickets relationship acyclic.)
- `_notification_outbox.py` must **not** import `_tickets`.
- `_action_log.py` must **not** import `_tickets`.
- No import cycles among store submodules.
- Routes (`app/main.py`) may call the store public API but should not run raw SQL.
- `app/db.py` must not import `app.main` or store domain modules.
- `app/security.py` must not import `app.main` or store domain modules.
- The frontend must not encode backend business rules that bypass backend
  validation (the server is always the source of truth).

When you need a name from another store module, import it from the **specific
submodule** (`from ._projects import get_project_by_key`), not from the facade.
