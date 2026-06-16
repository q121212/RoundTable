from fastapi.testclient import TestClient

from app import main
from app.main import app


def test_healthz_is_ok_without_auth(temp_db):
    client = TestClient(app)
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readyz_reports_ready_when_db_is_reachable(temp_db):
    client = TestClient(app)
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_readyz_returns_503_when_db_unavailable(temp_db, monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("db down")

    monkeypatch.setattr(main, "get_conn", boom)
    client = TestClient(app)
    response = client.get("/readyz")
    assert response.status_code == 503
    assert response.json()["status"] == "unavailable"
