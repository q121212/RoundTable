# RoundTable

RoundTable is a local, mobile-first Jira-like issue tracker for small teams,
solo developers, and AI-assisted development workflows.

It combines a lightweight web UI, HTTP API, GitHub App integration, MCP-style
endpoint, and notification system into a single local service built with
**FastAPI**, **Jinja**, **HTMX-ready templates**, and **SQLite**.

RoundTable treats its own tickets as the source of truth. GitHub can be
connected for branches, commits, and pull requests, but RoundTable does not try
to become a full GitHub Issues clone.

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
# Local-only convenience login:
# edit .env and set ALLOW_DEV_LOGIN=true if GitHub OAuth is not configured yet
uvicorn app.main:app --reload
```

Open <http://localhost:8000>. With `ALLOW_DEV_LOGIN=true`, the local login form
is available before GitHub OAuth is configured.

## Docker

```bash
cp .env.example .env
docker compose up --build
```

SQLite data lives in `./data/roundtable.db`.

## Deploy

`deploy.sh` supports the current server layout at `/srv/RoundTable`.

```bash
DEPLOY_HOST=deploy@example.com ./deploy.sh
```

By default it uses `DEPLOY_MODE=auto`: if `/srv/RoundTable/.git` exists on the
server, it deploys with `git pull`; otherwise it syncs the local working tree
with `rsync` while preserving `.env`, `.venv`, and `data/`.

Before exposing RoundTable publicly, deploy with:

```bash
DEPLOY_PUBLIC=true DEPLOY_HOST=deploy@example.com ./deploy.sh
```

Public deploy mode requires `BASE_URL=https://...`, `ALLOW_DEV_LOGIN=false`,
`SESSION_COOKIE_SECURE=true`, and signed webhooks in the server `.env`. Keep
uvicorn bound to `127.0.0.1:8380` and publish it through an HTTPS reverse proxy.

For public repo vs private server configuration separation, see
[docs/deployment-separation.md](docs/deployment-separation.md). In short: keep
RoundTable reusable and public, keep real server env/nginx/runbooks in a private
ops repo, and pass private deploy settings with `DEPLOY_ENV_FILE`.

## Features

- Projects with short keys like `CRM`, `OPS`, or `AI`.
- Project-prefixed ticket keys like `CRM-1`, `CRM-2`, and `OPS-1`.
- Ticket board with `Backlog`, `Todo`, `In Progress`, `Review`, `Done`, and `Closed`.
- Ticket details with title, markdown-ready description, status, priority,
  assignee, reporter, watchers, comments, GitHub links, and timestamps.
- Append-only `action_log` for important changes.
- Mobile-first UI: desktop kanban columns, phone status tabs, large touch
  targets, mobile status move controls, and no required horizontal scrolling.
- Live board updates through Server-Sent Events for ticket moves and edits.
- Quick display preferences: `en`/`ru` language switch and light/dark themes.
- GitHub App OAuth login and webhook-based linking for branches, commits, and PRs.
- MCP-style JSON-RPC endpoint for ticket automation.
- Email and Telegram notifications through a SQLite outbox with retries.

## Web Routes

```text
/
/projects
/p/{project_key}/board
/t/{ticket_key}
/settings/mcp
/settings/notifications
/integrations/github
```

## HTTP API

```text
POST   /api/projects
POST   /api/tickets
PATCH  /api/tickets/{key}
POST   /api/tickets/{key}/comments
POST   /api/tickets/{key}/close
POST   /api/tickets/{key}/reopen
POST   /api/tickets/{key}/watch
```

Notification routes:

```text
POST   /api/me/notifications/test
POST   /api/me/telegram/link
DELETE /api/me/telegram/link
PATCH  /api/me/notification-preferences
```

## GitHub Integration

Create a GitHub App with:

- OAuth callback URL: `${BASE_URL}/auth/github/callback`
- Webhook URL: `${BASE_URL}/integrations/github/webhook`
- Webhook secret matching `GITHUB_WEBHOOK_SECRET`
- Repository permissions for contents metadata, pull requests, and repository
  administration if you want automatic autolink creation.

Ticket keys like `CRM-123` are parsed from branch names, commit messages, pull
request titles, and pull request bodies. Supported webhook events include
`push`, `pull_request`, `create`, and `delete`.

Example autolink:

```text
CRM-123 -> https://host/t/CRM-123
```

## Auth And Permissions

RoundTable supports GitHub OAuth login with server-side sessions. For local
development, `ALLOW_DEV_LOGIN=true` enables a simple local login form.

Security-related behavior:

- server-side sessions
- CSRF protection
- role-based project access
- GitHub webhook signature validation
- MCP token hashing and revocation

Initial admins can be configured with:

```env
ADMIN_GITHUB_LOGINS=max,user2,user3
```

## MCP

Create a token in `/settings/mcp`, then connect a client to:

```text
POST /mcp
Authorization: Bearer rt_...
```

The endpoint supports:

- `initialize`
- `tools/list`
- `tools/call`
- `resources/list`
- `resources/read`

Implemented tools include project listing, ticket search/read/create/update,
status movement, assignment, comments, close/reopen, and GitHub ref linking.

Note: the current implementation is a lightweight MCP-compatible JSON-RPC
endpoint. The official Python MCP package was not available from the current
package index in this environment, so the dependency is not pinned yet.

## Notifications

RoundTable includes a notification system based on a SQLite outbox.

Supported channels:

- Telegram through Bot API as the primary phone notification channel
- Email through SMTP remains available in the worker, but the UI treats it as
  optional because GitHub profiles often do not expose email addresses

Notifications are queued, retried with exponential backoff, and filtered by
user preferences. Typical notification events are assignment, comments, status
movement, closing/reopening, and watcher-relevant updates.

Telegram linking uses a one-time token from `/settings/notifications`; the user
sends `/start <token>` to the configured bot. For public deployments, configure
Telegram's webhook `secret_token` and set the same value in
`TELEGRAM_WEBHOOK_SECRET`; RoundTable validates the
`X-Telegram-Bot-Api-Secret-Token` header.

## Configuration

See [.env.example](.env.example).

Important values:

```env
BASE_URL=http://localhost:8000
DATABASE_PATH=./data/roundtable.db
SECRET_KEY=change-me-long-random-string
ALLOW_DEV_LOGIN=false
ADMIN_GITHUB_LOGINS=your-github-login

GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
GITHUB_APP_ID=
GITHUB_APP_PRIVATE_KEY_PATH=
GITHUB_WEBHOOK_SECRET=

SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM=roundtable@localhost
SMTP_TLS=true

TELEGRAM_BOT_TOKEN=
TELEGRAM_WEBHOOK_SECRET=
```

## Data Model

Core entities:

```text
Project
Ticket
Comment
User
Watcher
GitHubLink
NotificationOutbox
NotificationPreference
McpToken
ActionLog
```

Design principles:

- ticket identity is based on project-prefixed keys
- ticket title does not need to repeat the project name
- important state changes are written to `action_log`
- GitHub links are secondary references, not the source of truth
- MCP access is token-based and checked through application permissions

## Tests

```bash
source .venv/bin/activate
pytest -q
ruff check .
python -m compileall app
```

The current suite covers ticket sequencing, status/action logging, notification
outbox behavior, GitHub webhook parsing, and MCP authentication/tool access.

## MVP Scope

Included:

- local web UI
- projects and ticket board
- ticket detail page
- comments and action log
- GitHub OAuth/webhook integration
- basic roles
- MCP-style endpoint and token management
- Email and Telegram notifications
- mobile-friendly responsive UI
- quick `en`/`ru` and light/dark display preferences

Out of scope for the MVP:

- full GitHub Issues synchronization
- separate native mobile app
- SMS notifications
- complex enterprise permission model
- multi-tenant SaaS hosting
