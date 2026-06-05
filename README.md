# RoundTable

RoundTable is a local, mobile-first Jira-like issue tracker designed for small teams, solo developers and AI-assisted development workflows.

It combines a lightweight web UI, HTTP API, GitHub App integration, MCP endpoint and notification system into a single local service built with **FastAPI**, **HTMX**, **Jinja** and **SQLite**.

The goal of RoundTable is to provide a practical project-tracking tool that is simple enough to run locally, but powerful enough to support real development workflows: tickets, boards, comments, activity history, GitHub links, automation via MCP and notifications through Email or Telegram.

---

## Key idea

RoundTable treats its own tickets as the source of truth.

GitHub can be connected for branches, commits and pull requests, but RoundTable does not try to become a full GitHub Issues clone. Instead, it provides a local Jira-like workflow with stable ticket keys such as:

```text
CRM-123
OPS-42
AI-7
````

Each project has a short key, and every ticket receives a project-prefixed identifier. These keys can be referenced from Git branches, commits, pull requests, chat messages, documentation and MCP tools.

---

## Features

### Projects and ticket keys

Each project has a short uppercase key such as:

* `CRM`
* `OPS`
* `AI`

Tickets are automatically numbered per project:

```text
CRM-1
CRM-2
OPS-1
AI-1
```

The ticket key is the main human-readable identity of the ticket.

---

### Ticket workflow

A ticket contains:

* title
* markdown description
* status
* priority
* assignee
* reporter
* watchers
* comments
* GitHub links
* timestamps
* append-only activity log

Supported statuses:

```text
Backlog
Todo
In Progress
Review
Done
Closed
```

Tickets can be:

* created
* edited
* assigned
* moved across statuses
* commented on
* watched
* closed
* reopened

Every important change is recorded in an append-only `action_log`, making the system auditable and useful for both humans and automation.

---

## Mobile-first web UI

RoundTable is designed to work well on both desktop and phone screens.

On desktop, the main project view uses a classic Kanban board with status columns.

On phones, the UI avoids uncomfortable horizontal boards and touch-based drag-and-drop. Instead, it uses:

* status tabs or filters
* compact ticket lists
* large touch targets
* bottom action bar
* mobile-friendly forms
* status change menus
* no required horizontal scrolling

This makes it possible to read, update and manage tickets from a phone without needing a separate mobile app.

---

## Web interface

Main web routes:

```text
/
 /projects
 /p/{project_key}/board
 /t/{ticket_key}
 /settings/mcp
 /settings/notifications
 /integrations/github
```

The web UI covers:

* project list
* project board
* ticket creation
* ticket editing
* ticket detail page
* comments
* activity log
* GitHub integration settings
* MCP token management
* notification settings

---

## HTTP API

RoundTable exposes a small HTTP API for internal UI actions and automation.

Example routes:

```text
POST   /api/projects
POST   /api/tickets
PATCH  /api/tickets/{key}
POST   /api/tickets/{key}/comments
POST   /api/tickets/{key}/close
POST   /api/tickets/{key}/reopen
POST   /api/tickets/{key}/watch
```

Notification-related routes:

```text
POST   /api/me/notifications/test
POST   /api/me/telegram/link
DELETE /api/me/telegram/link
PATCH  /api/me/notification-preferences
```

---

## GitHub integration

RoundTable supports GitHub App integration.

The GitHub App can:

* authenticate users through GitHub OAuth
* create autolinks for project ticket prefixes
* listen to GitHub webhooks
* connect tickets with branches, commits and pull requests

Example autolink:

```text
CRM-123 -> https://host/t/CRM-123
```

Supported GitHub events include:

* `push`
* `pull_request`
* `create`
* `delete`

This allows development activity to be attached to RoundTable tickets without making GitHub Issues the primary source of truth.

---

## Authentication and permissions

RoundTable uses GitHub App OAuth login with server-side sessions.

Security-related features:

* GitHub OAuth login
* server-side sessions
* CSRF protection
* role-based access
* GitHub webhook signature validation
* MCP token hashing
* MCP token revocation

Supported roles:

```text
admin
member
viewer
```

Initial admins can be configured through:

```env
ADMIN_GITHUB_LOGINS=max,user2,user3
```

---

## MCP endpoint

RoundTable exposes an MCP endpoint at:

```text
/mcp
```

The MCP server is built using the Python MCP SDK / FastMCP.

Users can create Bearer tokens from the UI. Tokens are stored hashed, can be revoked, and are used to authenticate MCP clients.

MCP tools can support:

* listing projects
* viewing boards
* reading tickets
* creating tickets
* updating tickets
* moving tickets between statuses
* assigning tickets
* adding comments
* closing tickets
* reopening tickets
* linking GitHub entities

This makes RoundTable suitable for AI-assisted workflows where an agent can inspect the board, create tasks, update progress or comment on tickets.

---

## Notifications

RoundTable includes a notification system based on a SQLite notification outbox.

Supported channels:

* Email through SMTP
* Telegram through Bot API

Notification delivery supports:

* queued outbox
* retries
* exponential backoff
* user preferences
* project-level mute/watch settings
* ticket-level mute/watch settings

Typical notification events:

* ticket assigned
* ticket commented
* ticket moved
* ticket closed
* watcher update
* GitHub activity linked to ticket

---

## Architecture

RoundTable is a single local service.

Suggested stack:

```text
FastAPI        application server and HTTP API
HTMX           dynamic UI without heavy frontend framework
Jinja          server-side templates
SQLite         local database
Python MCP SDK MCP endpoint
GitHub App     OAuth, autolinks and webhooks
SMTP           email notifications
Telegram Bot   phone notifications
Docker Compose deployment
```

The application is intentionally lightweight and easy to run locally.

---

## Deployment model

RoundTable is designed to run locally by default.

For production-like use, it can be deployed behind an HTTPS reverse proxy.

Expected deployment files:

```text
Dockerfile
docker-compose.yml
.env.example
```

Typical configuration includes:

```env
DATABASE_URL=sqlite:///data/roundtable.db
BASE_URL=https://roundtable.example.com

ADMIN_GITHUB_LOGINS=max

GITHUB_APP_ID=
GITHUB_APP_PRIVATE_KEY=
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
GITHUB_WEBHOOK_SECRET=

SMTP_HOST=
SMTP_PORT=
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM=

TELEGRAM_BOT_TOKEN=
```

---

## Data model overview

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

Important design principles:

* ticket identity is based on project-prefixed keys
* ticket title does not need to repeat the project name
* all important state changes are written to `action_log`
* GitHub links are secondary references, not the source of truth
* MCP access is token-based and scoped through application permissions

---

## Testing strategy

RoundTable should include tests for business logic, security, integrations and UI behavior.

### Unit tests

* project key validation
* per-project ticket sequencing
* status transitions
* permissions
* action log creation
* notification recipient resolution

### Security tests

* OAuth state validation
* CSRF protection
* MCP token hashing
* MCP token revocation
* GitHub webhook signature validation
* denied cross-project access

### GitHub integration tests

* mocked autolink setup
* branch parsing
* commit parsing
* pull request parsing
* webhook idempotency by delivery ID

### MCP tests

* authenticated tool calls
* unauthorized tool calls
* project-scoped access
* ticket CRUD through MCP
* status movement through MCP

### UI smoke tests

* create project
* create first ticket, for example `CRM-1`
* move ticket across board
* assign ticket
* add comment
* close ticket
* reopen ticket
* connect Telegram
* send test notification

### Responsive QA

Playwright checks should cover:

* desktop width
* tablet width
* phone width

Responsive checks should verify:

* no horizontal overflow
* readable ticket cards
* usable status switching
* visible primary actions
* mobile forms fit the screen
* large enough touch targets

---

## MVP scope

The MVP includes:

* local web UI
* projects
* ticket board
* ticket detail page
* comments
* action log
* GitHub OAuth login
* basic roles
* GitHub App webhook handling
* MCP endpoint
* MCP token management
* Email and Telegram notifications
* mobile-friendly responsive UI

Out of scope for the MVP:

* full GitHub Issues synchronization
* separate native mobile app
* SMS notifications
* complex enterprise permission model
* multi-tenant SaaS hosting

---

## Why RoundTable?

RoundTable is for workflows where a full Jira setup is too heavy, but plain GitHub Issues or TODO files are not enough.

It is especially useful when you want:

* local-first project tracking
* stable human-readable ticket keys
* lightweight Kanban workflow
* phone-friendly ticket management
* GitHub development activity linked to tickets
* AI agents that can read and update project state through MCP
* notifications without a large SaaS platform

RoundTable is designed to be small, understandable and hackable, while still covering the essential project-management loop.

