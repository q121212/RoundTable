import os
from dataclasses import dataclass
from typing import List

# Load a local .env if present so the documented `cp .env.example .env` workflow
# actually applies. Existing process env (e.g. systemd EnvironmentFile) wins.
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


def _bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _list(name: str) -> List[str]:
    return [item.strip() for item in os.getenv(name, "").split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "RoundTable")
    base_url: str = os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")
    database_path: str = os.getenv("DATABASE_PATH", "./data/roundtable.db")
    # Secure-by-default: dev login is an auth bypass (any login becomes admin),
    # so it must be opted into explicitly. Local dev keeps it on via .env.
    allow_dev_login: bool = _bool("ALLOW_DEV_LOGIN", False)
    # Startup refuses to run dev login together with an https BASE_URL (it looks
    # like production). This escape hatch re-enables that unsafe combination for
    # the rare case of an https preview that is genuinely private. Leave it off.
    allow_insecure_dev_login: bool = _bool("ALLOW_INSECURE_DEV_LOGIN", False)
    # Send the session cookie only over HTTPS. Defaults to on when BASE_URL is
    # https (i.e. a real deployment); off for local http dev. Override if needed.
    session_cookie_secure: bool = _bool(
        "SESSION_COOKIE_SECURE",
        os.getenv("BASE_URL", "http://localhost:8000").lower().startswith("https"),
    )
    # When the app runs behind a reverse proxy you trust (e.g. nginx), enable
    # this so the client IP used for rate limiting is read from the *last*
    # X-Forwarded-For hop (the one the proxy appended). Off by default: a direct
    # client must not be able to spoof its identity via the header.
    trust_proxy_headers: bool = _bool("TRUST_PROXY_HEADERS", False)

    admin_github_logins: List[str] = None  # type: ignore[assignment]

    github_client_id: str = os.getenv("GITHUB_CLIENT_ID", "")
    github_client_secret: str = os.getenv("GITHUB_CLIENT_SECRET", "")
    github_app_id: str = os.getenv("GITHUB_APP_ID", "")
    github_app_private_key_path: str = os.getenv("GITHUB_APP_PRIVATE_KEY_PATH", "")
    github_webhook_secret: str = os.getenv("GITHUB_WEBHOOK_SECRET", "")

    smtp_host: str = os.getenv("SMTP_HOST", "")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    smtp_from: str = os.getenv("SMTP_FROM", "roundtable@localhost")
    smtp_tls: bool = _bool("SMTP_TLS", True)

    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_webhook_secret: str = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")

    def __post_init__(self) -> None:
        object.__setattr__(self, "admin_github_logins", _list("ADMIN_GITHUB_LOGINS"))


settings = Settings()
