# RoundTable Load Testing

RoundTable is intentionally a single FastAPI process with SQLite. Load testing is
therefore a careful capacity probe, not a distributed benchmark. The goal is to
find the point where latency/error rate begins to bend, then stop before hurting
the shared server.

## Tool

Use the lightweight HTTP runner:

```bash
python tools/load_test.py --help
```

It creates tickets through the real web API with bounded concurrency and stops
when either threshold is crossed:

- error rate above `--max-error-rate` (default `2%`)
- p95 latency above `--max-p95-ms` (default `1500ms`)

The runner does not use Redis, background workers, npm, or a heavy load-test
framework. It uses `httpx`, already present in project dependencies.

## Local Smoke

Start local RoundTable with dev login enabled:

```bash
ALLOW_DEV_LOGIN=true BASE_URL=http://127.0.0.1:8000 uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Then run a tiny smoke:

```bash
python tools/load_test.py \
  --base-url http://127.0.0.1:8000 \
  --project-key LTLOCAL \
  --stages 1x5,2x10
```

This creates a test project and 15 tickets. Delete the project from the UI when
done.

## Production-Safe Probe

Never use dev login against production. Use an existing admin browser session and
copy:

- `roundtable_session` cookie into `ROUNDTABLE_SESSION`
- current CSRF token into `ROUNDTABLE_CSRF`

Then begin with tiny stages and generous pauses:

```bash
ROUNDTABLE_SESSION='...' \
ROUNDTABLE_CSRF='...' \
python tools/load_test.py \
  --base-url https://rt.aryx.me \
  --project-key LTSAFE \
  --stages 1x5,1x10,2x20 \
  --cooldown-s 15 \
  --min-delay-ms 150 \
  --max-p95-ms 1200 \
  --max-error-rate 0.01
```

Suggested ramp if the previous step is clean:

```text
1x5,1x10,2x20      smoke
2x50,3x75          light
4x100,6x150        moderate
8x250              stop here before discussing a heavier run
```

Do not jump to thousands of writes on the shared server. If p95 or errors bend
upward, stop and inspect the server before increasing the next stage.

## What To Watch

During a production-safe probe, watch the server in another terminal:

```bash
ssh hetz 'systemctl status roundtable --no-pager; journalctl -u roundtable -n 80 --no-pager'
ssh hetz 'top -b -n 1 | head -30; df -h /srv/RoundTable; du -h /srv/RoundTable/data/roundtable.db*'
```

Useful post-run checks:

```bash
ssh hetz 'sqlite3 /srv/RoundTable/data/roundtable.db "PRAGMA integrity_check;"'
ssh hetz 'curl -fsS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8380/login'
```

## Cleanup

Use a dedicated project key for load testing (`LTSAFE`, `LTLOCAL`, etc.). Delete
that project from the UI after the run. Do not run the tool against a real
project unless the goal is to deliberately test production data behavior.
