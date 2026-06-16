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
  notifications.py   in-process SQLite outbox loop (email + telegram)
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
- **Tickets:** project-prefixed keys (`GT-1`). Statuses, priorities, ticket types,
  sprints, story points, and ticket links are first-class product concepts.
  Statuses/priorities/types come from `db.py` (`TICKET_STATUSES`, `PRIORITIES`,
  `TICKET_TYPES`) — don't hardcode elsewhere. Important state changes are
  appended to `action_log`.
- **Project settings autosave:** project details, board statuses/types,
  statistics visibility, and ticket deletion policy autosave from
  `project_settings.html` via
  `setupProjectSettingsAutosave()`; don't reintroduce Save buttons for those
  sections unless the UX decision changes.
- **Statistics:** `/p/{project_key}/stats` summarizes tickets/story points by
  status, priority, type, assignee, and sprint. Visibility is project-configured
  (`all` by default, or project admins only).
- **Sprints:** projects may have multiple active sprints. The board's
  `Active sprints` filter is a view over all active sprints, not a singleton
  sprint selector. Activating a sprint must not silently deactivate another one.
- **Ticket deletion:** available only from the ticket page and only when allowed
  by the project's deletion policy. Default policy is project admins only. Keep
  confirmation-by-ticket-key and live board removal/count refresh intact.
- **Board edits:** keep cards compact (the board's value is fitting many tickets).
  Status changes by drag (pointer events) or inline `[data-inline-field]` → `PATCH
  /api/tickets/{key}`. Quick comments are handled through the compact comment chip
  popover → `POST .../comments`.
- **Notifications** go through the SQLite outbox + an in-process async loop;
  Telegram is a **per-user bot DM** (each user links their own chat). There is no
  shared channel. RoundTable is intentionally deployed as one app process with
  SQLite; do not add Redis, external queues, or multi-worker coordination unless
  the product decision changes.
- **Load testing:** use `tools/load_test.py` and `docs/load-testing.md`. Keep
  ramps small, use stop thresholds, and do not run large write tests against the
  shared server without an explicit go-ahead.

## Gotchas (learned the hard way)

- Static files are cached by the browser; hard-reload when verifying JS/CSS changes.

## Run / test / lint

```bash
python3.10 -m venv .venv && source .venv/bin/activate  # or newer
pip install -r requirements-dev.txt
cp .env.example .env
perl -0pi -e 's/ALLOW_DEV_LOGIN=false/ALLOW_DEV_LOGIN=true/' .env  # local dev only
uvicorn app.main:app --reload          # http://localhost:8000  (ALLOW_DEV_LOGIN=true)

pytest -q
ruff check .
python -m compileall app
```

Add a test for any behavior change in `app/store.py` or the API. Use the `temp_db`
fixture (`tests/conftest.py`).

## Deploy

`./deploy.sh` does SSH → `git pull` or local `rsync` (`DEPLOY_MODE=auto`) → venv
`pip install` → `systemctl restart` → healthcheck. Configure via `.env.deploy`
(gitignored) or flags; `DEPLOY_HOST` is required. The default server path is
`/srv/RoundTable`. Server runs under systemd — template in
`deploy/roundtable.service`. Use `DEPLOY_PUBLIC=true` for internet-facing deploys;
it fails unless the server `.env` has `BASE_URL=https://...`,
`ALLOW_DEV_LOGIN=false`, `SESSION_COOKIE_SECURE=true`, and signed webhook secrets
for enabled integrations. The app sets up its own schema on boot, so there is no
separate migration step.
For hardened servers, set `DEPLOY_APP_USER=roundtable` in the private deploy env;
`deploy.sh` will keep app files owned by that system user after rsync/build.

Keep this repo reusable/public. Real server inventory, `.env` values, nginx
configs with domains, and operational runbooks belong in the private ops repo
`git@github.com:q121212/RoundTable-Ops.git` or on the server. Use
`DEPLOY_ENV_FILE` to source private deploy settings from outside this repo. See
`docs/deployment-separation.md`.

For the current shared server, deploy from this repo with:

```bash
DEPLOY_PUBLIC=true DEPLOY_ENV_FILE=../RoundTable-Ops/env/adv_msk02.env ./deploy.sh
```

Do not hand-edit application files on the server for routine releases; update this
repo, push it, then deploy with the script so `/srv/RoundTable` stays reproducible.
