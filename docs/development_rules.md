# Development rules

Rules for changing RoundTable safely. Layer/dependency rules live in
[architecture.md](architecture.md); this file covers events, i18n, deploy/ops,
and the process for larger changes. Where a rule is machine-checked, the test is
named.

## Event / audit rules

A "no-op" edit is an update that resolves to no semantic change (e.g. setting a
ticket field to the value it already has).

- A no-op update **must not** write an `action_log` row.
- A no-op update **must not** publish an SSE / project event.
- A no-op update **must not** trigger a frontend notification sound (a
  consequence of not publishing an event).
- Only **actual** semantic changes should log to `action_log` and publish.

How it works today: `store.update_ticket` returns the ticket with a private
`_changed` flag; `main.publish_ticket_event` skips broadcasting when
`_changed is False`. If you change `update_ticket` or `publish_ticket_event`,
keep these invariants and update the regression tests.

Guarded by `tests/test_ticket_events.py` (no `action_log` row + no SSE event for
a no-op; both written for a real change).

## i18n rules

- All user-facing frontend strings must have an i18n key (`data-i18n`,
  `-placeholder`, `-tooltip`, `-aria`) resolved from the `messages` dict in
  `app/static/app.js`.
- The RU locale must **not** silently fall back to English for visible labels
  (`translate()` falls back to `en` when a key is missing — that is the bug
  class we guard against). Product names and technical constants (e.g.
  "RoundTable", "GitHub", "Telegram", "MCP", "SP") may stay as-is.
- When you add a visible label, add the key to **every** locale (`en` and `ru`).
- Add/extend a frontend contract assertion for new structural labels.

Guarded by `tests/test_frontend_contracts.py`:
`test_all_i18n_keys_exist_in_every_locale` (en/ru key sets must be identical)
and `test_user_facing_strings_are_translated_in_both_languages` (specific
templates carry `data-i18n`).

## Deploy / ops rules

- `deploy.sh` must preserve `data/`, `.env`, `.venv/`, and `backups/` (they are
  rsync `--exclude`d).
- Deploy must take a SQLite backup with an integrity check before restart.
- Deploy must healthcheck `/readyz`.
- An app-only deploy may restart **only** `roundtable.service`.
- Changing **Caddy / HAProxy / firewall (ufw/nft/iptables) / systemd units** is
  an infrastructure change and requires separate, explicit approval — never from
  application code or a routine deploy.
- `TRUST_PROXY_HEADERS` must remain `false` on the current HAProxy→Caddy L4
  (SNI passthrough) topology: the real client IP does not reach the app, so
  trusting `X-Forwarded-For` would gain nothing and could be spoofed. Only change
  this if the proxy topology is deliberately changed (e.g. PROXY protocol added),
  as a reviewed infra change.

The host is multi-tenant — other services run alongside RoundTable. Never
restart, stop, reconfigure, or otherwise touch them.

## Process for architecture changes

If a change requires any of:

- crossing layer boundaries (e.g. a route doing raw SQL, a store submodule
  importing `app.main`),
- adding a new allowed dependency direction,
- introducing new infrastructure (Redis, a queue, another database, a cache),
- creating a new long-lived background process,

then write a short ADR/RFC **first** (a markdown note under `docs/` is enough)
covering:

1. **Problem** — what forces the change.
2. **Options** — at least two, with trade-offs.
3. **Chosen approach** — and why.
4. **Dependency impact** — which layers/edges change; update
   `architecture.md` and the guard tests.
5. **Rollback** — how to revert safely.
6. **Tests** — what proves it works and prevents regression.

Keep RoundTable single-process + SQLite unless an ADR explicitly justifies
otherwise. Do not add Redis/Postgres/Celery/queues without that approval.
