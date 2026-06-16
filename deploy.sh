#!/usr/bin/env bash
#
# Simple one-command deploy for RoundTable (SSH + systemd + venv).
#
#   auto mode:
#     - if the server path is a git checkout: git pull
#     - otherwise: rsync this local working tree to the server
#   then: venv pip install -> restart service -> healthcheck
#
# The app runs schema setup itself on startup (init_db), so there is no separate
# migration step. SQLite data lives under ./data and is left untouched.
#
# Config: set values via env, a gitignored .env.deploy next to this script, an
# external DEPLOY_ENV_FILE from a private ops repo, or pass flags. Required:
# DEPLOY_HOST.
#
#   DEPLOY_HOST        ssh target, e.g. deploy@example.com   (required)
#   DEPLOY_PATH        app dir on server        (default: /srv/RoundTable)
#   DEPLOY_BRANCH      git branch to deploy     (default: main)
#   DEPLOY_SERVICE     systemd unit name        (default: roundtable)
#   DEPLOY_HEALTH_URL  url checked after restart(default: http://127.0.0.1:8380/login)
#   DEPLOY_PYTHON      Python 3.10+ on server   (default: python3)
#   DEPLOY_MODE        auto | git | rsync       (default: auto)
#   DEPLOY_PUBLIC      true requires safe public .env settings
#   DEPLOY_ENV_FILE    optional private deploy env file to source
#   DEPLOY_APP_USER    optional system user that owns/runs the app
#   DEPLOY_APP_GROUP   optional system group; defaults to DEPLOY_APP_USER
#   DEPLOY_BACKUP      true runs an online SQLite backup before restart
#
# Usage:
#   ./deploy.sh                          # uses env / .env.deploy
#   ./deploy.sh --host deploy@example.com --path /srv/RoundTable --mode auto
#   DEPLOY_PUBLIC=true ./deploy.sh --host deploy@example.com
#
set -euo pipefail

cd "$(dirname "$0")"
if [ -n "${DEPLOY_ENV_FILE:-}" ]; then
  if [ ! -f "$DEPLOY_ENV_FILE" ]; then
    echo "error: DEPLOY_ENV_FILE does not exist: $DEPLOY_ENV_FILE" >&2
    exit 2
  fi
  set -a
  . "$DEPLOY_ENV_FILE"
  set +a
elif [ -f .env.deploy ]; then
  set -a
  . ./.env.deploy
  set +a
fi

HOST="${DEPLOY_HOST:-}"
APP_DIR="${DEPLOY_PATH:-/srv/RoundTable}"
BRANCH="${DEPLOY_BRANCH:-main}"
SERVICE="${DEPLOY_SERVICE:-roundtable}"
HEALTH_URL="${DEPLOY_HEALTH_URL:-http://127.0.0.1:8380/login}"
PY="${DEPLOY_PYTHON:-python3}"
MODE="${DEPLOY_MODE:-auto}"
PUBLIC="${DEPLOY_PUBLIC:-false}"
APP_USER="${DEPLOY_APP_USER:-}"
APP_GROUP="${DEPLOY_APP_GROUP:-${APP_USER:-}}"
BACKUP="${DEPLOY_BACKUP:-$PUBLIC}"

while [ $# -gt 0 ]; do
  case "$1" in
    --host)    HOST="$2"; shift 2 ;;
    --path)    APP_DIR="$2"; shift 2 ;;
    --branch)  BRANCH="$2"; shift 2 ;;
    --service) SERVICE="$2"; shift 2 ;;
    --health)  HEALTH_URL="$2"; shift 2 ;;
    --mode)    MODE="$2"; shift 2 ;;
    --public)  PUBLIC=true; shift ;;
    -h|--help) sed -n '2,30p' "$0"; exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done

if [ -z "$HOST" ]; then
  echo "error: DEPLOY_HOST is not set (use --host user@server or .env.deploy)" >&2
  exit 2
fi

if [ "$MODE" != "auto" ] && [ "$MODE" != "git" ] && [ "$MODE" != "rsync" ]; then
  echo "error: DEPLOY_MODE must be auto, git, or rsync (got '$MODE')" >&2
  exit 2
fi

echo "==> Deploying to $HOST:$APP_DIR (service: $SERVICE, mode: $MODE)"

remote_has_git=false
if ssh "$HOST" "test -d '$APP_DIR/.git'"; then
  remote_has_git=true
fi

effective_mode="$MODE"
if [ "$effective_mode" = "auto" ]; then
  if [ "$remote_has_git" = true ]; then
    effective_mode=git
  else
    effective_mode=rsync
  fi
fi

echo "==> Effective mode: $effective_mode"

if [ "$effective_mode" = "git" ] && [ "$remote_has_git" != true ]; then
  echo "error: $APP_DIR is not a git checkout on $HOST; use --mode rsync or --mode auto" >&2
  exit 2
fi

if [ "$effective_mode" = "rsync" ]; then
  if ! command -v rsync >/dev/null 2>&1; then
    echo "error: rsync is required for rsync deploy mode" >&2
    exit 2
  fi
  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "==> Local revision: $(git rev-parse --short HEAD)$(git diff --quiet || echo '+dirty')"
  fi
  echo "==> Syncing local working tree to server"
  ssh "$HOST" "mkdir -p '$APP_DIR'"
  rsync -az --delete \
    --no-owner \
    --no-group \
    --exclude '.git/' \
    --exclude '.venv/' \
    --exclude '.env' \
    --exclude '.env.deploy' \
    --exclude '.pytest_cache/' \
    --exclude '.ruff_cache/' \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    --exclude '.DS_Store' \
    --exclude 'data/' \
    ./ "$HOST:$APP_DIR/"
fi

# Remote build/restart. Local vars are expanded here, then run on the server.
ssh "$HOST" "APP_DIR='$APP_DIR' BRANCH='$BRANCH' SERVICE='$SERVICE' PY='$PY' MODE='$effective_mode' PUBLIC='$PUBLIC' APP_USER='$APP_USER' APP_GROUP='$APP_GROUP' BACKUP='$BACKUP' bash -s" <<'REMOTE'
set -euo pipefail
cd "$APP_DIR"

ensure_app_user() {
  if [ -z "${APP_USER:-}" ]; then
    return
  fi
  if ! id "$APP_USER" >/dev/null 2>&1; then
    echo "--> create app user $APP_USER"
    sudo useradd --system --home "$APP_DIR" --shell /usr/sbin/nologin "$APP_USER"
  fi
  if [ -n "${APP_GROUP:-}" ] && ! getent group "$APP_GROUP" >/dev/null 2>&1; then
    sudo groupadd --system "$APP_GROUP"
  fi
}

fix_app_ownership() {
  if [ -z "${APP_USER:-}" ]; then
    return
  fi
  local group="${APP_GROUP:-$APP_USER}"
  echo "--> set app ownership to $APP_USER:$group"
  sudo chown -R "$APP_USER:$group" "$APP_DIR"
  if [ -f "$APP_DIR/.env" ]; then
    sudo chmod 0640 "$APP_DIR/.env"
  fi
  if [ -d "$APP_DIR/data" ]; then
    sudo find "$APP_DIR/data" -type d -exec chmod 0750 {} +
    sudo find "$APP_DIR/data" -type f -name '*.db*' -exec chmod 0640 {} +
  fi
}

ensure_app_user

if [ "$MODE" = "git" ]; then
  echo "--> git fetch & fast-forward"
  git fetch --all --prune
  git checkout "$BRANCH"
  git pull --ff-only origin "$BRANCH"
fi

if [ ! -f .env ]; then
  echo "error: $APP_DIR/.env is missing; create it from .env.example and edit secrets" >&2
  exit 1
fi

env_get() {
  awk -F= -v key="$1" '$1 == key {print substr($0, index($0, "=") + 1); exit}' .env
}

BASE_URL="$(env_get BASE_URL)"
ALLOW_DEV_LOGIN="$(env_get ALLOW_DEV_LOGIN)"
SESSION_COOKIE_SECURE="$(env_get SESSION_COOKIE_SECURE)"
GITHUB_WEBHOOK_SECRET="$(env_get GITHUB_WEBHOOK_SECRET)"
TELEGRAM_BOT_TOKEN="$(env_get TELEGRAM_BOT_TOKEN)"
TELEGRAM_WEBHOOK_SECRET="$(env_get TELEGRAM_WEBHOOK_SECRET)"
DATABASE_PATH="$(env_get DATABASE_PATH)"

echo "--> deployment env summary"
echo "    BASE_URL=${BASE_URL:-<unset>}"
echo "    ALLOW_DEV_LOGIN=${ALLOW_DEV_LOGIN:-<unset>}"
echo "    SESSION_COOKIE_SECURE=${SESSION_COOKIE_SECURE:-<auto>}"

if [ "${ALLOW_DEV_LOGIN,,}" = "true" ]; then
  echo "warning: ALLOW_DEV_LOGIN=true. This is only safe for a private SSH/local preview." >&2
fi

if [ "${PUBLIC,,}" = "true" ]; then
  case "$BASE_URL" in
    https://*) ;;
    *) echo "error: DEPLOY_PUBLIC=true requires BASE_URL=https://..." >&2; exit 1 ;;
  esac
  if [ "${ALLOW_DEV_LOGIN,,}" = "true" ]; then
    echo "error: DEPLOY_PUBLIC=true requires ALLOW_DEV_LOGIN=false" >&2
    exit 1
  fi
  if [ "${SESSION_COOKIE_SECURE,,}" != "true" ]; then
    echo "error: DEPLOY_PUBLIC=true requires SESSION_COOKIE_SECURE=true" >&2
    exit 1
  fi
  if [ -z "${GITHUB_WEBHOOK_SECRET:-}" ]; then
    echo "error: DEPLOY_PUBLIC=true requires GITHUB_WEBHOOK_SECRET for signed GitHub webhooks" >&2
    exit 1
  fi
  if [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -z "${TELEGRAM_WEBHOOK_SECRET:-}" ]; then
    echo "error: DEPLOY_PUBLIC=true with TELEGRAM_BOT_TOKEN requires TELEGRAM_WEBHOOK_SECRET" >&2
    exit 1
  fi
fi

backup_sqlite() {
  local database="${DATABASE_PATH:-./data/roundtable.db}"
  case "$database" in
    /*) ;;
    *) database="$APP_DIR/$database" ;;
  esac
  if [ ! -f "$database" ]; then
    echo "--> SQLite backup skipped: database does not exist yet ($database)"
    return
  fi
  local backup_dir="$APP_DIR/backups"
  local backup_file="$backup_dir/roundtable-$(date -u +%Y%m%dT%H%M%SZ).db"
  mkdir -p "$backup_dir"
  echo "--> SQLite backup: $backup_file"
  DB_SRC="$database" DB_DEST="$backup_file" "$PY" - <<'PYBACKUP'
import os
import sqlite3

src = os.environ["DB_SRC"]
dest = os.environ["DB_DEST"]
source = sqlite3.connect(src)
try:
    target = sqlite3.connect(dest)
    try:
        source.backup(target)
        result = target.execute("PRAGMA integrity_check").fetchone()[0]
        if result != "ok":
            raise SystemExit(f"backup integrity_check failed: {result}")
    finally:
        target.close()
finally:
    source.close()
PYBACKUP
  chmod 0640 "$backup_file" || true
}

if [ "${BACKUP,,}" = "true" ]; then
  backup_sqlite
fi

echo "--> python deps"
"$PY" - <<'PYMIN'
import sys
if sys.version_info < (3, 10):
    raise SystemExit("RoundTable requires Python 3.10+")
PYMIN
if [ -d .venv ] && ! ./.venv/bin/python - <<'PYMIN'
import sys
raise SystemExit(0 if sys.version_info >= (3, 10) else 1)
PYMIN
then
  echo "--> existing .venv uses old Python; recreating"
  rm -rf .venv
fi
if [ ! -d .venv ]; then "$PY" -m venv .venv; fi
./.venv/bin/python -m pip install --upgrade pip --quiet
./.venv/bin/python -m pip install -r requirements.txt --quiet
fix_app_ownership

echo "--> restart service"
sudo systemctl restart "$SERVICE"
sleep 2
sudo systemctl is-active --quiet "$SERVICE" || { echo "service '$SERVICE' is not active"; sudo journalctl -u "$SERVICE" -n 40 --no-pager; exit 1; }
echo "--> service active"
REMOTE

echo "==> Healthcheck $HEALTH_URL"
code="$(ssh "$HOST" "curl -fsS -o /dev/null -w '%{http_code}' '$HEALTH_URL' || true")"
if [ "$code" = "200" ] || [ "$code" = "303" ]; then
  echo "==> OK ($code) — deploy finished"
else
  echo "==> Healthcheck failed (got '$code')" >&2
  exit 1
fi
