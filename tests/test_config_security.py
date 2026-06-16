import pytest

from app.config import settings
from app.main import enforce_secure_startup


@pytest.fixture()
def settings_guard():
    """Snapshot and restore the settings this module mutates so global state
    does not leak into other tests (Settings is a frozen dataclass)."""
    keys = ["allow_dev_login", "base_url", "allow_insecure_dev_login"]
    saved = {key: getattr(settings, key) for key in keys}
    yield
    for key, value in saved.items():
        object.__setattr__(settings, key, value)


def _set(allow_dev_login, base_url, allow_insecure=False):
    object.__setattr__(settings, "allow_dev_login", allow_dev_login)
    object.__setattr__(settings, "base_url", base_url)
    object.__setattr__(settings, "allow_insecure_dev_login", allow_insecure)


def test_dev_login_on_https_refuses_to_start(settings_guard):
    _set(True, "https://rt.example.test")
    with pytest.raises(RuntimeError):
        enforce_secure_startup()


def test_dev_login_on_http_is_allowed(settings_guard):
    _set(True, "http://localhost:8000")
    enforce_secure_startup()  # must not raise


def test_dev_login_off_on_https_is_allowed(settings_guard):
    _set(False, "https://rt.example.test")
    enforce_secure_startup()  # must not raise


def test_escape_hatch_allows_insecure_dev_login(settings_guard):
    _set(True, "https://rt.example.test", allow_insecure=True)
    enforce_secure_startup()  # explicit override, must not raise
