# Deployment Separation

RoundTable is intended to be a public, reusable application repository. Keep
server-specific operations separate from this repo.

## Public RoundTable Repo

Safe to keep public:

- application code
- tests
- generic deployment script (`deploy.sh`)
- generic systemd/nginx examples
- `.env.example` with safe defaults
- `deploy/env.deploy.example` with placeholder values only

Never commit here:

- real `.env` or `.env.deploy`
- SSH targets and private hostnames if they are not intentionally public
- OAuth client secrets, webhook secrets, SMTP passwords, Telegram tokens
- real TLS private keys or nginx files containing secrets
- production database files from `data/`

## Private Ops Repo

Our private ops repo is `git@github.com:q121212/RoundTable-Ops.git`.
It is the canonical place for deployment notes about the `adv_msk02_root`
server, nginx publication choices, and operator runbooks. Keep it private.

Suggested layout:

```text
RoundTable-Ops/
  README.md
  env/
    adv_msk02.env              # deploy.sh inputs, no app secrets unless needed
  server/
    roundtable.env.example     # redacted app env template
    nginx-roundtable.conf      # real domain/proxy config
    roundtable.service         # installed systemd unit if customized
  runbooks/
    publish.md
    rollback.md
```

Run deploy from the public repo while sourcing private deploy settings:

```bash
DEPLOY_ENV_FILE=../RoundTable-Ops/env/adv_msk02.env ./deploy.sh
```

For an internet-facing rollout:

```bash
DEPLOY_PUBLIC=true DEPLOY_ENV_FILE=../RoundTable-Ops/env/adv_msk02.env ./deploy.sh
```

`DEPLOY_PUBLIC=true` intentionally fails unless the server-side app `.env` is
safe for public access:

```env
BASE_URL=https://roundtable.example.com
ALLOW_DEV_LOGIN=false
SESSION_COOKIE_SECURE=true
```

## Server

Secrets should ultimately live on the server, not in either repo:

```text
/srv/RoundTable/.env
/srv/RoundTable/data/roundtable.db
```

Keep uvicorn private:

```text
127.0.0.1:8380
```

Expose RoundTable through HTTPS reverse proxy only.

## Plain Directory Deployments

If `/srv/RoundTable` is a plain copied directory rather than a git checkout,
`deploy.sh` handles it with `DEPLOY_MODE=auto`, which falls back to `rsync` while
preserving server-only `.env`, `.venv`, and `data/`.
