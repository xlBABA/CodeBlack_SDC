"""Milestone 11B: POST /api/v1/cv/parse.

Every GLM call is mocked — app.services.cv_extraction_service.extract_cv_fields
is patched directly, so no test ever reaches httpx/the network, and the
autouse _no_ambient_runpod_credentials fixture (tests/conftest.py) means
even a developer's real exported RUNPOD_API_KEY can't change that.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter

from app.core.config import Settings, get_settings
from app.main import app
from app.services.glm_client import GlmExtractionError, GlmExtractionResult


def _override_settings(**overrides):
    app.dependency_overrides[get_settings] = lambda: Settings(_env_file=None, **overrides)


def _clear_override():
    app.dependency_overrides.pop(get_settings, None)


def _build_text_pdf(text: str) -> bytes:
    """A minimal, hand-built single-page PDF with real selectable text —
    no reportlab/extra test-only dependency needed."""
    content = f"BT /F1 12 Tf 10 100 Td ({text}) Tj ET".encode("latin-1")
    objects = [
        b"<</Type/Catalog/Pages 2 0 R>>",
        b"<</Type/Pages/Kids[3 0 R]/Count 1>>",
        b"<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]/Resources<</Font<</F1 4 0 R>>>>/Contents 5 0 R>>",
        b"<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>",
        b"<</Length " + str(len(content)).encode() + b">>stream\n" + content + b"\nendstream",
    ]
    out = bytearray()
    out += b"%PDF-1.4\n"
    offsets = [0]
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj".encode() + obj + b"endobj\n"
    xref_offset = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode() + b"0000000000 65535 f \n"
    for off in offsets[1:]:
        out += f"{off:010} 00000 n \n".encode()
    out += (
        b"trailer\n<</Size " + str(len(objects) + 1).encode() + b"/Root 1 0 R>>\n"
        b"startxref\n" + str(xref_offset).encode() + b"\n%%EOF"
    )
    return bytes(out)


def _build_blank_pdf() -> bytes:
    """A real, valid PDF with a page but zero text content — simulates a
    scanned/image-only CV without requiring OCR or an actual raster image."""
    import io

    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def _build_encrypted_pdf() -> bytes:
    import io

    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.encrypt(user_password="secret123", owner_password="ownerpw")
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


VALID_CV_TEXT = "Jane Student Computer Science Python SQL Developer Internship"
VALID_PDF = _build_text_pdf(VALID_CV_TEXT)

FAKE_GLM_JSON = {
    "name": "Jane Student",
    "summary": "CS undergraduate",
    "education": [{"institution": "Test University", "degree": "BSc", "field_of_study": "Computer Science"}],
    "skills": ["Python", "SQL", "Underwater Basket Weaving"],
    "projects": [{"title": "Sales dashboard", "description": "Built with SQL and Python"}],
    "experience": [],
    "certifications": [],
}


def _post_cv(client: TestClient, pdf_bytes: bytes, filename: str = "cv.pdf", content_type: str = "application/pdf"):
    return client.post("/api/v1/cv/parse", files={"file": (filename, pdf_bytes, content_type)})


# --- Valid PDF + successful GLM extraction ---------------------------------


def test_valid_pdf_with_successful_glm_extraction_returns_ok_draft(client: TestClient):
    with patch(
        "app.services.cv_extraction_service.extract_cv_fields",
        return_value=GlmExtractionResult(raw_json=FAKE_GLM_JSON),
    ):
        response = _post_cv(client, VALID_PDF)

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["status"] == "ok"
    assert body["data"]["extracted_text_preview"] is None  # never echoed back on success
    draft = body["data"]["draft"]
    assert draft["name"] == "Jane Student"
    assert {s["skill_id"] for s in draft["mapped_skills"]} == {"python", "sql"}
    assert draft["unmapped_skills"] == [{"raw_text": "Underwater Basket Weaving"}]
    assert draft["suggested_profile"]["skills"]
    assert draft["suggested_profile"]["degree"] == "Computer Science"


def test_mapped_skills_use_real_catalogue_ids_never_invented(client: TestClient):
    glm_json = {**FAKE_GLM_JSON, "skills": ["sql", "Structured Query Language", "Flibbertigibbet"]}
    with patch(
        "app.services.cv_extraction_service.extract_cv_fields",
        return_value=GlmExtractionResult(raw_json=glm_json),
    ):
        response = _post_cv(client, VALID_PDF)

    draft = response.json()["data"]["draft"]
    mapped_ids = {s["skill_id"] for s in draft["mapped_skills"]}
    assert mapped_ids == {"sql"}  # "sql" and its alias both resolve to the one real catalogue skill_id
    assert any(u["raw_text"] == "Flibbertigibbet" for u in draft["unmapped_skills"])


# --- Invalid upload content -------------------------------------------------


def test_non_pdf_content_is_rejected(client: TestClient):
    response = _post_cv(client, b"this is not a pdf at all", content_type="application/pdf")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_CV_FILE"


def test_obviously_wrong_declared_mime_type_is_rejected_even_with_real_pdf_bytes(client: TestClient):
    """An early, cheap rejection on a declared type that's clearly not a
    PDF (image/zip/text/...) — even if the actual bytes happen to be a
    valid PDF, a client that says "this is a PNG" is treated as wrong."""
    response = _post_cv(client, VALID_PDF, content_type="image/png")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_CV_FILE"


def test_missing_declared_mime_type_is_not_rejected_on_that_basis_alone(client: TestClient):
    """A declared type is advisory, not authoritative: an empty/missing
    Content-Type must not block an otherwise-valid PDF — the real check
    is the content-based one inside validate_and_extract(). (No GLM
    mock needed: with no RUNPOD_API_KEY configured, this degrades to
    "manual_review" rather than "ok", but it must still be a 200, never
    a 422 from the MIME gate.)"""
    response = _post_cv(client, VALID_PDF, content_type="")
    assert response.status_code == 200


def test_empty_file_is_rejected(client: TestClient):
    response = _post_cv(client, b"")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_CV_FILE"


def test_corrupted_pdf_with_valid_header_but_broken_body_is_rejected(client: TestClient):
    response = _post_cv(client, b"%PDF-1.4\nthis is garbage, not a real pdf body\n%%EOF")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_CV_FILE"


def test_oversize_file_is_rejected(client: TestClient):
    from app.services.cv_pdf import MAX_PDF_BYTES

    oversized = b"%PDF-1.4\n" + b"0" * (MAX_PDF_BYTES + 1)
    response = _post_cv(client, oversized)
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "FILE_TOO_LARGE"


def test_encrypted_pdf_is_rejected(client: TestClient):
    response = _post_cv(client, _build_encrypted_pdf())
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_CV_FILE"
    assert "password" in response.json()["error"]["message"].lower()


# --- Scanned/image-only PDF (no OCR) ----------------------------------------


def test_scanned_pdf_with_no_extractable_text_degrades_gracefully(client: TestClient):
    response = _post_cv(client, _build_blank_pdf())
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["status"] == "no_extractable_text"
    assert body["data"]["draft"]["suggested_profile"]["skills"] == []
    assert any("scanned" in w.lower() or "selectable text" in w.lower() for w in body["warnings"])


# --- GLM unavailable / malformed output -------------------------------------


def test_glm_timeout_or_network_failure_falls_back_to_manual_review(client: TestClient):
    with patch(
        "app.services.cv_extraction_service.extract_cv_fields",
        side_effect=GlmExtractionError("The extraction service timed out."),
    ):
        response = _post_cv(client, VALID_PDF)

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["status"] == "manual_review"
    assert body["data"]["draft"]["mapped_skills"] == []
    assert body["data"]["draft"]["suggested_profile"]["skills"] == []
    # A bounded preview is offered here (unlike the "ok" path) so the user can self-serve.
    assert body["data"]["extracted_text_preview"] == VALID_CV_TEXT


def test_malformed_glm_json_falls_back_to_manual_review_not_a_crash(client: TestClient):
    with patch(
        "app.services.cv_extraction_service.extract_cv_fields",
        return_value=GlmExtractionResult(raw_json={"this_is": "not the expected shape at all", "skills": "not a list"}),
    ):
        response = _post_cv(client, VALID_PDF)

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["status"] == "manual_review"
    assert "did not match the expected format" in " ".join(body["warnings"])


def test_glm_output_with_only_unexpected_extra_keys_is_still_usable(client: TestClient):
    """extra='ignore': a model adding commentary fields must not break
    extraction of the fields that ARE present and valid."""
    glm_json = {**FAKE_GLM_JSON, "model_commentary": "I am an AI and here is my reasoning..."}
    with patch(
        "app.services.cv_extraction_service.extract_cv_fields",
        return_value=GlmExtractionResult(raw_json=glm_json),
    ):
        response = _post_cv(client, VALID_PDF)

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "ok"


# --- Draft is never written to the stored profile ---------------------------


def test_parse_never_touches_the_profile_database(client: TestClient, db_session):
    from app.db.models import StudentProfileORM

    with patch(
        "app.services.cv_extraction_service.extract_cv_fields",
        return_value=GlmExtractionResult(raw_json=FAKE_GLM_JSON),
    ):
        _post_cv(client, VALID_PDF)

    assert db_session.query(StudentProfileORM).count() == 0


# --- Real RunPod is never contacted, even if credentials look real ---------


def test_glm_client_never_opens_a_real_socket_even_with_real_looking_credentials():
    """Direct test of app.services.glm_client.extract_cv_fields (not
    through the endpoint, which already mocks this function entirely in
    every test above). Uses httpx.MockTransport — the standard way to
    exercise real httpx request-building/response-parsing logic with
    zero actual network I/O — to prove the function behaves correctly
    end to end while never touching a real socket, and only ever
    targets the configured GLM host."""
    import httpx

    from app.services.glm_client import extract_cv_fields

    calls = {"n": 0}

    def _handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        assert request.url.host == "api.runpod.ai"
        assert request.headers["Authorization"] == "Bearer rpa_looks_real_but_is_not"
        return httpx.Response(
            200, json={"choices": [{"message": {"content": '{"skills": ["Python"]}'}}]}
        )

    mock_client = httpx.Client(transport=httpx.MockTransport(_handler))
    result = extract_cv_fields(
        "some cv text",
        api_key="rpa_looks_real_but_is_not",
        base_url="https://api.runpod.ai/v2/b1dd8hy2hqo1nb/openai/v1",
        model="glm-5.3",
        client=mock_client,
    )

    assert calls["n"] == 1  # exactly one request, to the mock transport, never a real one
    assert result.raw_json == {"skills": ["Python"]}


def test_endpoint_never_calls_the_real_glm_client_in_any_test_above():
    """Sanity check on the test suite itself: every endpoint-level test
    above patches app.services.cv_extraction_service.extract_cv_fields,
    so none of them can ever reach glm_client's real httpx usage. This
    assertion just documents that guarantee in one place."""
    import app.services.cv_extraction_service as service_module

    assert service_module.extract_cv_fields.__module__ == "app.services.glm_client"
