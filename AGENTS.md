# AGENTS.md — RoundTable

Conventions and architecture for anyone (human or AI: Codex, Claude, etc.) editing
this repo. Keep it short and current. `CLAUDE.md` imports this file, so both tools
read the same rules — edit **this** file, not a copy.

## What it is

RoundTable is a local, self-hosted, Jira-like ticket tracker for small teams and
AI-assisted workflows. Tickets are the source of truth; GitHub is a secondary link.
See `README.md` for the product tour.

## Stack & philosophy

- **Backend:** FastAPI (`app/main.py`) + Jinja2 server-rendered templates.
- **Data:** SQLite via stdlib `sqlite3`. All SQL lives in `app/store.py`; schema in
  `app/db.py`.
- **Frontend:** plain CSS (`app/static/styles.css`) + vanilla JS (`app/static/app.js`).
  **No build step, no npm, no framework.** HTMX is loaded but board interactions are
  hand-written vanilla JS (pointer-event drag & drop, `fetch` for inline updates).
- Keep it dependency-light and server-rendered. Don't introduce a JS framework or a
  bundler without a strong reason.

## Layout

```
app/
  main.py            FastAPI routes (pages + JSON/form API)
  store.py           data layer — ALL sql goes here
  db.py              schema + init_db(); TICKET_STATUSES, PRIORITIES
  security.py        sessions, CSRF, hashing, webhook signatures
  notifications.py   SQLite outbox worker (email + telegram)
  github_integration.py / mcp_server.py
  templates/*.html   Jinja pages (extend base.html)
  static/app.js      i18n, theming, board DnD, inline edits
  static/styles.css  design tokens + components
tests/               pytest suite
deploy.sh, deploy/   deployment (see below)
```

## Conventions that bite if ignored

- **CSRF on every mutation.** All state-changing requests pass through
  `validate_csrf_request` (`security.py`). Send the token as the `x-csrf-token`
  header (JSON/AJAX) **or** a `csrf_token` form field. The board reads it from
  `.board[data-csrf]`.
- **i18n is client-side.** UI strings use `data-i18n` (and `-placeholder`, `-tooltip`,
  `-aria`) attributes resolved from the `messages` dict in `app.js`. When you add user
  text, add the key to **both** `en` and `ru` in `app.js`; templates hold the English
  default.
- **Theming via CSS variables.** Tokens are defined in `:root` / `:root[data-theme="dark"]`.
  Note `styles.css` has a later "Current UI pass" block that **overrides** earlier
  values — change tokens there, and check both light and dark.
- **No migration framework.** `init_db()` runs on startup and uses
  `CREATE TABLE IF NOT EXISTS`. Schema changes must be additive and safe against
  existing DBs; there is no down-migration. SQLite file lives in `./data/`.
- **Tickets:** project-prefixed keys (`GT-1`). Statuses and priorities come from
  `db.py` (`TICKET_STATUSES`, `PRIORITIES`) — don't hardcode elsewhere. Important
  state changes are appended to `action_log`.
- **Board edits:** keep cards compact (the board's value is fitting many tickets).
  Status changes by drag (pointer events) or inline `[data-inline-field]` → `PATCH
  /api/tickets/{key}`. Quick comment `[data-inline-comment]` → `POST .../comments`.
- **Notifications** go through the SQLite outbox + background worker; Telegram is a
  **per-user bot DM** (each user links their own chat). There is no shared channel.

## Gotchas (learned the hard way)

- **Build `FormData` before disabling inputs.** Disabled fields are dropped from
  `FormData`, which silently sends an empty body. (Bit the quick-comment handler.)
- `update_ticket`'s no-op path returns a bare ticket row **without** the assignee join
  fields; the join fields only come from the change path.
- Static files are cached by the browser; hard-reload when verifying JS/CSS changes.

## Run / test / lint

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:app --reload          # http://localhost:8000  (ALLOW_DEV_LOGIN=true)

pytest -q
ruff check .
python -m compileall app
```

Add a test for any behavior change in `app/store.py` or the API. Use the `temp_db`
fixture (`tests/conftest.py`).

## Deploy

`./deploy.sh` does SSH → `git pull` → venv `pip install` → `systemctl restart` →
healthcheck. Configure via `.env.deploy` (gitignored) or flags; `DEPLOY_HOST` is
required. Server runs under systemd — template in `deploy/roundtable.service`. The app
sets up its own schema on boot, so there is no separate migration step.
