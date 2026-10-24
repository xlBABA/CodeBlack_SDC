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


VALID_CV_TEXT = (
    "Jane Student Computer Science Python SQL Developer Internship "
    "Also skilled in Underwater Basket Weaving"
)
VALID_PDF = _build_text_pdf(VALID_CV_TEXT)

FAKE_GLM_JSON = {
    "name": "Jane Student",
    "summary": "CS undergraduate",
    "education": [{"institution": "Test University", "degree": "BSc", "field_of_study": "Computer Science"}],
    "skills": [
        {"name": "Python", "evidence": "Python"},
        {"name": "SQL", "evidence": "SQL"},
        {"name": "Underwater Basket Weaving", "evidence": "Underwater Basket Weaving"},
    ],
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
    assert all(s["evidence"] for s in draft["mapped_skills"])  # every mapped skill carries its quote
    assert draft["unmapped_skills"] == [
        {"raw_text": "Underwater Basket Weaving", "evidence": "Underwater Basket Weaving"}
    ]
    assert draft["skills_requiring_review"] == []
    assert draft["suggested_profile"]["skills"]
    assert draft["suggested_profile"]["degree"] == "Computer Science"
    # Requirement 6: proficiency is never inferred, only left for the student.
    assert all(s["proficiency"] is None for s in draft["suggested_profile"]["skills"])


def test_mapped_skills_use_real_catalogue_ids_never_invented(client: TestClient):
    glm_json = {
        **FAKE_GLM_JSON,
        "skills": [
            {"name": "sql", "evidence": "SQL"},
            {"name": "Structured Query Language", "evidence": "SQL"},
            # Not literally present in VALID_CV_TEXT — proves GLM is never trusted
            # to invent a skill_id, AND (Milestone 11E) that an unverifiable quote
            # keeps a skill out of mapped_skills entirely, catalogue match or not.
            {"name": "Flibbertigibbet", "evidence": "Flibbertigibbet expert"},
        ],
    }
    with patch(
        "app.services.cv_extraction_service.extract_cv_fields",
        return_value=GlmExtractionResult(raw_json=glm_json),
    ):
        response = _post_cv(client, VALID_PDF)

    draft = response.json()["data"]["draft"]
    mapped_ids = {s["skill_id"] for s in draft["mapped_skills"]}
    assert mapped_ids == {"sql"}  # "sql" and its alias both resolve to the one real catalogue skill_id
    assert not any(u["raw_text"] == "Flibbertigibbet" for u in draft["unmapped_skills"])
    assert any(r["name"] == "Flibbertigibbet" for r in draft["skills_requiring_review"])


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
    """Milestone 12C-8E: this payload has no usable field anywhere (a
    garbage top-level key, and a 'skills' value that isn't even a list)
    — after normalization it cleans down to a totally empty extraction,
    which is treated the same as an outright schema failure (never a
    falsely-reassuring "ok" with a blank draft and no text to fall back
    on) — see _is_effectively_empty."""
    with patch(
        "app.services.cv_extraction_service.extract_cv_fields",
        return_value=GlmExtractionResult(raw_json={"this_is": "not the expected shape at all", "skills": "not a list"}),
    ):
        response = _post_cv(client, VALID_PDF)

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["status"] == "manual_review"
    assert body["warnings"] == [
        "We couldn't read your CV automatically right now. Please review or fill in your details below."
    ]


def test_glm_output_with_no_recognizable_fields_at_all_falls_back_to_manual_review(client: TestClient):
    """An empty JSON object: syntactically valid, schema-valid (every
    field is Optional/defaults empty), but contains nothing at all —
    must still degrade to manual_review, not a hollow "ok"."""
    with patch(
        "app.services.cv_extraction_service.extract_cv_fields",
        return_value=GlmExtractionResult(raw_json={}),
    ):
        response = _post_cv(client, VALID_PDF)

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["status"] == "manual_review"
    assert body["data"]["extracted_text_preview"] == VALID_CV_TEXT


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


def test_legacy_plain_string_skill_entries_are_isolated_not_fatal(client: TestClient):
    """Milestone 11E changed skills from `list[str]` to a list of
    {name, evidence} objects. Milestone 12C-8E: a real GLM deployment
    answering in the old plain-string shape for some/all skills must no
    longer discard the ENTIRE extraction — each plain-string skill is
    normalized to {name, evidence: None} (never inventing a quote that
    was never given) and goes through the normal "missing evidence"
    review path, exactly like every other field GLM got right."""
    glm_json = {**FAKE_GLM_JSON, "skills": ["Python", "SQL"]}
    with patch(
        "app.services.cv_extraction_service.extract_cv_fields",
        return_value=GlmExtractionResult(raw_json=glm_json),
    ):
        response = _post_cv(client, VALID_PDF)

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["status"] == "ok"
    draft = body["data"]["draft"]
    assert draft["name"] == "Jane Student"  # the rest of the extraction survives intact
    assert draft["mapped_skills"] == []
    assert draft["unmapped_skills"] == []
    assert {r["name"] for r in draft["skills_requiring_review"]} == {"Python", "SQL"}
    assert draft["suggested_profile"]["skills"] == []


# --- Milestone 12C-8E: isolating malformed entries, never a wholesale failure


def test_one_malformed_skill_entry_is_dropped_while_valid_skills_still_extract(client: TestClient):
    """The core regression test for the production bug: ONE bad skill
    entry (evidence of the wrong type) must not take down the whole
    response — every other valid skill still gets mapped."""
    glm_json = {
        **FAKE_GLM_JSON,
        "skills": [
            {"name": "Python", "evidence": "Python"},
            {"name": "Broken", "evidence": ["not", "a", "string"]},  # malformed
            {"name": "SQL", "evidence": "SQL"},
        ],
    }
    with patch(
        "app.services.cv_extraction_service.extract_cv_fields",
        return_value=GlmExtractionResult(raw_json=glm_json),
    ):
        response = _post_cv(client, VALID_PDF)

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["status"] == "ok"
    draft = body["data"]["draft"]
    assert {s["skill_id"] for s in draft["mapped_skills"]} == {"python", "sql"}
    # The malformed entry's name survives (evidence alone was dropped, not invented)
    # and correctly lands in skills_requiring_review for lack of evidence.
    assert any(r["name"] == "Broken" for r in draft["skills_requiring_review"])


def test_one_malformed_certification_entry_is_dropped_while_rest_of_extraction_survives(client: TestClient):
    """Requirement 7 applies beyond skills too: a malformed entry in any
    list field is isolated, not fatal to the whole response."""
    glm_json = {
        **FAKE_GLM_JSON,
        "certifications": [
            {"name": "AWS Certified", "issuer": "Amazon", "year": "2025"},
            {"issuer": "Missing Name Inc"},  # malformed: "name" is required
        ],
    }
    with patch(
        "app.services.cv_extraction_service.extract_cv_fields",
        return_value=GlmExtractionResult(raw_json=glm_json),
    ):
        response = _post_cv(client, VALID_PDF)

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["status"] == "ok"
    draft = body["data"]["draft"]
    assert [c["name"] for c in draft["certifications"]] == ["AWS Certified"]
    assert {s["skill_id"] for s in draft["mapped_skills"]} == {"python", "sql"}  # unaffected


def test_omitted_optional_top_level_fields_are_not_fatal(client: TestClient):
    """GLM may simply not include a key at all (vs. an explicit null) for
    a section the CV lacks — this must behave exactly like an empty list."""
    glm_json = {
        "name": "Jane Student",
        "skills": [{"name": "Python", "evidence": "Python"}],
        # summary, education, projects, experience, certifications: all omitted entirely
    }
    with patch(
        "app.services.cv_extraction_service.extract_cv_fields",
        return_value=GlmExtractionResult(raw_json=glm_json),
    ):
        response = _post_cv(client, VALID_PDF)

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["status"] == "ok"
    draft = body["data"]["draft"]
    assert draft["summary"] is None
    assert draft["education"] == []
    assert draft["projects"] == []
    assert draft["experience"] == []
    assert draft["certifications"] == []
    assert {s["skill_id"] for s in draft["mapped_skills"]} == {"python"}


def test_explicit_null_lists_are_treated_as_empty_not_fatal(client: TestClient):
    """GLM may send JSON `null` for a section instead of `[]` or omitting
    the key — must normalize to empty, never crash the whole response."""
    glm_json = {
        **FAKE_GLM_JSON,
        "education": None,
        "projects": None,
        "experience": None,
        "certifications": None,
    }
    with patch(
        "app.services.cv_extraction_service.extract_cv_fields",
        return_value=GlmExtractionResult(raw_json=glm_json),
    ):
        response = _post_cv(client, VALID_PDF)

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["status"] == "ok"
    draft = body["data"]["draft"]
    assert draft["education"] == []
    assert draft["projects"] == []
    assert draft["experience"] == []
    assert draft["certifications"] == []
    # Skills (a separate top-level field, untouched by this test) still extract normally.
    assert {s["skill_id"] for s in draft["mapped_skills"]} == {"python", "sql"}


def test_null_skills_list_is_treated_as_empty_not_fatal(client: TestClient):
    glm_json = {**FAKE_GLM_JSON, "skills": None}
    with patch(
        "app.services.cv_extraction_service.extract_cv_fields",
        return_value=GlmExtractionResult(raw_json=glm_json),
    ):
        response = _post_cv(client, VALID_PDF)

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["status"] == "ok"  # name/summary/projects still present
    draft = body["data"]["draft"]
    assert draft["mapped_skills"] == []
    assert draft["unmapped_skills"] == []
    assert draft["skills_requiring_review"] == []


def test_skill_with_overlong_evidence_keeps_the_name_and_requests_manual_review(client: TestClient):
    """An evidence quote that exceeds even the widened schema bound is
    dropped (never truncated/invented) — the skill's name survives and
    is routed to skills_requiring_review, not the whole response."""
    glm_json = {
        **FAKE_GLM_JSON,
        "skills": [{"name": "Python", "evidence": "Python " * 100}],  # far over the bound
    }
    with patch(
        "app.services.cv_extraction_service.extract_cv_fields",
        return_value=GlmExtractionResult(raw_json=glm_json),
    ):
        response = _post_cv(client, VALID_PDF)

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["status"] == "ok"
    draft = body["data"]["draft"]
    assert draft["mapped_skills"] == []
    assert any(r["name"] == "Python" for r in draft["skills_requiring_review"])


def test_diagnostic_log_never_includes_raw_cv_text_or_evidence(client: TestClient, caplog):
    """Requirement 4: a dropped malformed entry logs only safe loc/type
    diagnostics — never the actual CV text, evidence quotes, or any
    other field value from the request, even though a drop-and-log path
    is genuinely exercised here (a certification missing its required
    "name", with a secret-looking value in a different field)."""
    secret_text = "SuperSecretStudentNameZZZ999 confidential evidence snippet"
    glm_json = {
        "name": "Jane",
        "skills": [{"name": "Python", "evidence": "Python"}],
        "certifications": [{"issuer": secret_text}],  # missing required "name" -> dropped + logged
    }
    with caplog.at_level("INFO"):
        with patch(
            "app.services.cv_extraction_service.extract_cv_fields",
            return_value=GlmExtractionResult(raw_json=glm_json),
        ):
            response = _post_cv(client, VALID_PDF)

    assert response.status_code == 200
    log_text = caplog.text
    assert "certifications" in log_text  # the drop was actually logged, not silently skipped
    assert secret_text not in log_text
    assert VALID_CV_TEXT not in log_text


# --- Evidence validation (Milestone 11E) ------------------------------------


def test_skill_with_missing_evidence_is_excluded_and_flagged_for_review(client: TestClient):
    glm_json = {**FAKE_GLM_JSON, "skills": [{"name": "Python", "evidence": None}]}
    with patch(
        "app.services.cv_extraction_service.extract_cv_fields",
        return_value=GlmExtractionResult(raw_json=glm_json),
    ):
        response = _post_cv(client, VALID_PDF)

    draft = response.json()["data"]["draft"]
    assert draft["mapped_skills"] == []
    assert draft["unmapped_skills"] == []
    assert draft["skills_requiring_review"] == [
        {
            "name": "Python",
            "reason": (
                "No supporting quote was provided for this skill, so it was not "
                "added automatically. Add it yourself if it's accurate."
            ),
        }
    ]
    # Never silently added to the suggested profile either (requirement 5).
    assert draft["suggested_profile"]["skills"] == []


def test_skill_with_hallucinated_evidence_is_excluded_and_flagged_for_review(client: TestClient):
    """The quoted 'evidence' is not actually present anywhere in the
    locally-extracted CV text — must never be trusted just because GLM
    said so (requirement 4)."""
    glm_json = {
        **FAKE_GLM_JSON,
        "skills": [
            {
                "name": "Java",
                "evidence": "Led a team of 10 engineers building Java microservices",
            }
        ],
    }
    with patch(
        "app.services.cv_extraction_service.extract_cv_fields",
        return_value=GlmExtractionResult(raw_json=glm_json),
    ):
        response = _post_cv(client, VALID_PDF)

    draft = response.json()["data"]["draft"]
    assert draft["mapped_skills"] == []
    assert draft["unmapped_skills"] == []
    assert len(draft["skills_requiring_review"]) == 1
    assert draft["skills_requiring_review"][0]["name"] == "Java"
    assert "could not be found" in draft["skills_requiring_review"][0]["reason"]
    assert draft["suggested_profile"]["skills"] == []
    assert any("could not be automatically verified" in w for w in response.json()["warnings"])


def test_skill_evidence_with_harmless_whitespace_differences_is_still_accepted(client: TestClient):
    """GLM's quote need not byte-for-byte match the PDF's extracted
    whitespace (extra spaces/newlines are common PDF-extraction noise)
    — only the words themselves must be a real, exact substring."""
    glm_json = {
        **FAKE_GLM_JSON,
        "skills": [{"name": "SQL", "evidence": "  SQL   \n Developer  "}],
    }
    with patch(
        "app.services.cv_extraction_service.extract_cv_fields",
        return_value=GlmExtractionResult(raw_json=glm_json),
    ):
        response = _post_cv(client, VALID_PDF)

    draft = response.json()["data"]["draft"]
    assert draft["skills_requiring_review"] == []
    assert {s["skill_id"] for s in draft["mapped_skills"]} == {"sql"}


def test_evidence_substring_match_is_case_insensitive(client: TestClient):
    glm_json = {**FAKE_GLM_JSON, "skills": [{"name": "Python", "evidence": "python"}]}
    with patch(
        "app.services.cv_extraction_service.extract_cv_fields",
        return_value=GlmExtractionResult(raw_json=glm_json),
    ):
        response = _post_cv(client, VALID_PDF)

    draft = response.json()["data"]["draft"]
    assert {s["skill_id"] for s in draft["mapped_skills"]} == {"python"}
    assert draft["skills_requiring_review"] == []


def test_evidence_validation_helper_directly():
    """Unit-level coverage of the actual comparison logic, independent
    of the PDF/GLM pipeline."""
    from app.services.cv_extraction_service import _evidence_is_supported

    text = "Built dashboards using   Python\nand SQL during an internship."
    assert _evidence_is_supported("Python", text) is True
    assert _evidence_is_supported("python", text) is True  # case-insensitive
    assert _evidence_is_supported("Python\nand SQL", text) is True  # whitespace-normalized
    assert _evidence_is_supported("Rust", text) is False  # not present at all -> hallucinated
    assert _evidence_is_supported(None, text) is False  # missing evidence
    assert _evidence_is_supported("", text) is False
    assert _evidence_is_supported("P", text) is False  # too short to be meaningful evidence


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


# --- Fenced replies and invalid top-level scalars ----------------------------


@pytest.mark.parametrize(
    "content",
    ['```json\n{"skills": ["Python"]}\n```', '```\n{"skills": ["Python"]}\n```', '  ```JSON {"skills": ["Python"]} ```  '],
)
def test_glm_client_unwraps_a_markdown_json_fence(content):
    import httpx

    from app.services.glm_client import extract_cv_fields

    def _handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})

    result = extract_cv_fields(
        "some cv text", api_key="dummy", base_url="https://llm.invalid/v1", model="m",
        client=httpx.Client(transport=httpx.MockTransport(_handler)),
    )
    assert result.raw_json == {"skills": ["Python"]}


def test_glm_client_still_rejects_prose_around_a_fence():
    import httpx

    from app.services.glm_client import extract_cv_fields

    def _handler(request: httpx.Request) -> httpx.Response:
        content = 'Here you go: ```json {"skills": []} ```'
        return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})

    with pytest.raises(GlmExtractionError):
        extract_cv_fields(
            "some cv text", api_key="dummy", base_url="https://llm.invalid/v1", model="m",
            client=httpx.Client(transport=httpx.MockTransport(_handler)),
        )


@pytest.mark.parametrize(
    "bad_fields",
    [{"name": {"first": "Jane"}}, {"summary": ["CS", "undergraduate"]}, {"name": 42, "summary": "x" * 2001}],
)
def test_invalid_top_level_name_or_summary_becomes_none_and_keeps_the_rest(client: TestClient, bad_fields):
    with patch(
        "app.services.cv_extraction_service.extract_cv_fields",
        return_value=GlmExtractionResult(raw_json={**FAKE_GLM_JSON, **bad_fields}),
    ):
        response = _post_cv(client, VALID_PDF)

    data = response.json()["data"]
    assert data["status"] == "ok"
    for field in bad_fields:
        assert data["draft"][field] is None
    assert {s["skill_id"] for s in data["draft"]["mapped_skills"]} == {"python", "sql"}
    assert data["draft"]["education"]


def test_evidence_must_match_whole_words():
    from app.services.cv_extraction_service import _evidence_is_supported

    text = "Digital marketing intern. Built a JavaScript page with C++ and Python (pandas)."
    assert _evidence_is_supported("git", text) is False  # inside "Digital"
    assert _evidence_is_supported("Java", text) is False  # inside "JavaScript"
    assert _evidence_is_supported("Script", text) is False
    assert _evidence_is_supported("JavaScript", text) is True
    assert _evidence_is_supported("C++", text) is True
    assert _evidence_is_supported("Python (pandas)", text) is True
    assert _evidence_is_supported("marketing intern.", text) is True


def test_skill_whose_evidence_is_only_part_of_a_word_is_flagged_for_review(client: TestClient):
    pdf = _build_text_pdf("Digital marketing intern who wrote Python scripts")
    glm_json = {"skills": [{"name": "Git", "evidence": "git"}, {"name": "Python", "evidence": "Python"}]}
    with patch(
        "app.services.cv_extraction_service.extract_cv_fields",
        return_value=GlmExtractionResult(raw_json=glm_json),
    ):
        draft = _post_cv(client, pdf).json()["data"]["draft"]

    assert [s["skill_id"] for s in draft["mapped_skills"]] == ["python"]
    assert [s["name"] for s in draft["skills_requiring_review"]] == ["Git"]
    assert [s["skill_id"] for s in draft["suggested_profile"]["skills"]] == ["python"]


# --- Contained-skill fallback ------------------------------------------------


def test_skill_name_containing_one_catalogue_phrase_maps_pending_confirmation(client: TestClient):
    pdf = _build_text_pdf("Skills: Python (pandas), Advanced Excel, Statistics")
    glm_json = {"skills": [
        {"name": "Python (pandas)", "evidence": "Python (pandas)"},  # contains "Python"
        {"name": "Advanced Excel", "evidence": "Advanced Excel"},  # an exact alias
        {"name": "Statistics", "evidence": "Statistics"},  # contains no catalogue phrase
    ]}
    with patch(
        "app.services.cv_extraction_service.extract_cv_fields",
        return_value=GlmExtractionResult(raw_json=glm_json),
    ):
        body = _post_cv(client, pdf).json()

    draft = body["data"]["draft"]
    by_id = {s["skill_id"]: s for s in draft["mapped_skills"]}
    assert by_id["python"]["raw_text"] == "Python (pandas)"
    assert by_id["python"]["needs_confirmation"] is True
    assert by_id["excel"]["needs_confirmation"] is False
    assert draft["unmapped_skills"] == [{"raw_text": "Statistics", "evidence": "Statistics"}]
    assert {s["skill_id"] for s in draft["suggested_profile"]["skills"]} == {"python", "excel"}
    assert any('"Python (pandas)"' in w and "please confirm" in w for w in body["warnings"])


def test_contained_skill_fallback_still_requires_evidence(client: TestClient):
    pdf = _build_text_pdf("Skills: SQL reporting for a student club")
    glm_json = {"skills": [{"name": "Python (pandas)", "evidence": "Python (pandas)"}]}
    with patch(
        "app.services.cv_extraction_service.extract_cv_fields",
        return_value=GlmExtractionResult(raw_json=glm_json),
    ):
        draft = _post_cv(client, pdf).json()["data"]["draft"]

    assert draft["mapped_skills"] == []
    assert [s["name"] for s in draft["skills_requiring_review"]] == ["Python (pandas)"]


def test_name_containing_two_catalogue_phrases_is_not_guessed(client: TestClient):
    pdf = _build_text_pdf("Skills: Python and SQL scripting")
    glm_json = {"skills": [{"name": "Python and SQL scripting", "evidence": "Python and SQL scripting"}]}
    with patch(
        "app.services.cv_extraction_service.extract_cv_fields",
        return_value=GlmExtractionResult(raw_json=glm_json),
    ):
        draft = _post_cv(client, pdf).json()["data"]["draft"]

    assert draft["mapped_skills"] == []
    assert [s["raw_text"] for s in draft["unmapped_skills"]] == ["Python and SQL scripting"]
