import os
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.config import settings  # noqa: E402
from app.db import init_db  # noqa: E402


@pytest.fixture()
def temp_db(tmp_path):
    db_path = tmp_path / "roundtable-test.db"
    object.__setattr__(settings, "database_path", str(db_path))
    object.__setattr__(settings, "admin_github_logins", [])
    object.__setattr__(settings, "allow_dev_login", True)
    object.__setattr__(settings, "base_url", "http://testserver")
    object.__setattr__(settings, "github_webhook_secret", "")
    object.__setattr__(settings, "telegram_webhook_secret", "")
    init_db()
    return db_path
