from fastapi.testclient import TestClient
from trading_bot.api.main import app

def test_ping():
    client = TestClient(app)
    resp = client.get("/ping")
    assert resp.status_code == 200
    assert resp.json().get("status") == "ok"
