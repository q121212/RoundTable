import os
from dataclasses import dataclass
from typing import List


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
    secret_key: str = os.getenv("SECRET_KEY", "dev-roundtable-secret-change-me")
    allow_dev_login: bool = _bool("ALLOW_DEV_LOGIN", True)
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

    def __post_init__(self) -> None:
        object.__setattr__(self, "admin_github_logins", _list("ADMIN_GITHUB_LOGINS"))


settings = Settings()

