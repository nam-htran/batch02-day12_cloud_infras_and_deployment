from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "Container is alive"}

def test_ready():
    response = client.get("/ready")
    # Tùy thuộc vào Redis có đang bật hay không lúc test
    assert response.status_code in [200, 503]

def test_ask_no_api_key():
    response = client.post("/ask", json={"question": "hello"})
    assert response.status_code == 401
