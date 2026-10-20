from fastapi.testclient import TestClient


def test_health_endpoint_contract(client: TestClient):
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "ok"
    assert isinstance(body["version"], str)
    assert isinstance(body["dependencies"], dict)
    assert body["dependencies"]["database"] == "ok"
