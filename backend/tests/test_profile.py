from fastapi.testclient import TestClient

from app.fixtures.sample_profiles import SAMPLE_PROFILES

VALID_PAYLOAD = SAMPLE_PROFILES["cs_undergrad_data"].model_dump(exclude_none=True)


def test_openapi_includes_profile_analyze():
    from app.main import app

    schema = app.openapi()
    assert "/api/v1/profile/analyze" in schema["paths"]
    assert "post" in schema["paths"]["/api/v1/profile/analyze"]


def test_create_profile_returns_contract_shape(client: TestClient):
    response = client.post("/api/v1/profile/analyze", json=VALID_PAYLOAD)
    assert response.status_code == 200

    body = response.json()
    assert body["data_mode"] == "live"
    assert isinstance(body["generated_at"], str)
    assert body["warnings"] == []

    data = body["data"]
    assert data["profile_id"].startswith("profile_")
    assert data["degree"] == "Computer Science"
    assert {s["skill_id"] for s in data["skills"]} == {"sql", "python"}


def test_update_existing_profile_via_same_endpoint(client: TestClient):
    created = client.post("/api/v1/profile/analyze", json=VALID_PAYLOAD).json()
    profile_id = created["data"]["profile_id"]

    update_payload = dict(VALID_PAYLOAD)
    update_payload["profile_id"] = profile_id
    update_payload["degree"] = "Information Systems"
    update_payload["skills"] = [VALID_PAYLOAD["skills"][0]]

    response = client.post("/api/v1/profile/analyze", json=update_payload)
    assert response.status_code == 200

    data = response.json()["data"]
    assert data["profile_id"] == profile_id
    assert data["degree"] == "Information Systems"
    assert [s["skill_id"] for s in data["skills"]] == ["sql"]


def test_unknown_profile_id_returns_404_error_envelope(client: TestClient):
    payload = dict(VALID_PAYLOAD)
    payload["profile_id"] = "profile_does_not_exist"

    response = client.post("/api/v1/profile/analyze", json=payload)
    assert response.status_code == 404

    body = response.json()
    assert body["error"]["code"] == "PROFILE_NOT_FOUND"
    assert "request_id" in body


def test_missing_required_field_returns_422_error_envelope(client: TestClient):
    payload = dict(VALID_PAYLOAD)
    del payload["skills"]

    response = client.post("/api/v1/profile/analyze", json=payload)
    assert response.status_code == 422

    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert isinstance(body["error"]["details"], list)
    assert "request_id" in body


def test_invalid_skill_proficiency_returns_422(client: TestClient):
    payload = dict(VALID_PAYLOAD)
    payload["skills"] = [{"skill_id": "sql", "name": "SQL", "proficiency": "expert"}]

    response = client.post("/api/v1/profile/analyze", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_invalid_semester_returns_422(client: TestClient):
    payload = dict(VALID_PAYLOAD)
    payload["semester"] = 0

    response = client.post("/api/v1/profile/analyze", json=payload)
    assert response.status_code == 422


def test_multiple_profiles_no_cross_contamination(client: TestClient):
    first = client.post("/api/v1/profile/analyze", json=VALID_PAYLOAD).json()["data"]

    second_payload = SAMPLE_PROFILES["business_finance_student"].model_dump(exclude_none=True)
    second = client.post("/api/v1/profile/analyze", json=second_payload).json()["data"]

    assert first["profile_id"] != second["profile_id"]
    assert first["degree"] != second["degree"]
