#!/usr/bin/env bash
#
# Simple one-command deploy for RoundTable (SSH + systemd + venv).
#
#   on the server:  git pull -> venv pip install -> restart service -> healthcheck
#
# The app runs schema setup itself on startup (init_db), so there is no separate
# migration step. SQLite data lives under ./data and is left untouched.
#
# Config: set values via env or a gitignored .env.deploy next to this script,
# or pass flags. Required: DEPLOY_HOST.
#
#   DEPLOY_HOST        ssh target, e.g. deploy@example.com   (required)
#   DEPLOY_PATH        app dir on server        (default: /opt/roundtable)
#   DEPLOY_BRANCH      git branch to deploy     (default: main)
#   DEPLOY_SERVICE     systemd unit name        (default: roundtable)
#   DEPLOY_HEALTH_URL  url checked after restart(default: http://127.0.0.1:8000/login)
#   DEPLOY_PYTHON      python on server         (default: python3)
#
# Usage:
#   ./deploy.sh                          # uses env / .env.deploy
#   ./deploy.sh --host deploy@host --path /srv/roundtable --branch main
#
set -euo pipefail

cd "$(dirname "$0")"
[ -f .env.deploy ] && set -a && . ./.env.deploy && set +a

HOST="${DEPLOY_HOST:-}"
APP_DIR="${DEPLOY_PATH:-/opt/roundtable}"
BRANCH="${DEPLOY_BRANCH:-main}"
SERVICE="${DEPLOY_SERVICE:-roundtable}"
HEALTH_URL="${DEPLOY_HEALTH_URL:-http://127.0.0.1:8000/login}"
PY="${DEPLOY_PYTHON:-python3}"

while [ $# -gt 0 ]; do
  case "$1" in
    --host)    HOST="$2"; shift 2 ;;
    --path)    APP_DIR="$2"; shift 2 ;;
    --branch)  BRANCH="$2"; shift 2 ;;
    --service) SERVICE="$2"; shift 2 ;;
    --health)  HEALTH_URL="$2"; shift 2 ;;
    -h|--help) sed -n '2,30p' "$0"; exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done

if [ -z "$HOST" ]; then
  echo "error: DEPLOY_HOST is not set (use --host user@server or .env.deploy)" >&2
  exit 2
fi

echo "==> Deploying '$BRANCH' to $HOST:$APP_DIR (service: $SERVICE)"

# Remote build/restart. Local vars are expanded here, then run on the server.
ssh "$HOST" "APP_DIR='$APP_DIR' BRANCH='$BRANCH' SERVICE='$SERVICE' PY='$PY' bash -s" <<'REMOTE'
set -euo pipefail
cd "$APP_DIR"

echo "--> git fetch & fast-forward"
git fetch --all --prune
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"

echo "--> python deps"
if [ ! -d .venv ]; then "$PY" -m venv .venv; fi
./.venv/bin/python -m pip install --upgrade pip --quiet
./.venv/bin/python -m pip install -r requirements.txt --quiet

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
