import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1.endpoints.careers import reset_shared_hussain_provider_for_tests
from app.db import models  # noqa: F401  (registers ORM tables on Base.metadata)
from app.db.session import Base, get_db
from app.main import app


@pytest.fixture(autouse=True)
def _reset_shared_hussain_provider():
    """Milestone 10B: get_matching_provider() now reuses one
    HussainMatchingProvider across requests (so its RunPod circuit
    breaker persists in production) — reset it before and after every
    test so a RunPod failure/cooldown simulated in one test (in any test
    file; pytest runs them all in one process) never leaks into another
    test's assertions."""
    reset_shared_hussain_provider_for_tests()
    yield
    reset_shared_hussain_provider_for_tests()


@pytest.fixture(autouse=True)
def _no_ambient_runpod_credentials(monkeypatch):
    """Milestone 10D: mirrors app/services/hussain_matching/tests/
    conftest.py's own no_runpod_env fixture, extended to every test in
    this directory too (not just his vendored package's own tests).
    MATCHING_MODE=hussain is now exercised throughout backend/tests/ with
    get_matching_provider() no longer forcing a no-similarity override
    (Milestone 10A) — without this, a developer's real exported
    RUNPOD_API_KEY/RUNPOD_ENDPOINT_ID (e.g. for manual testing against
    Hussain's real deployed endpoint) would silently leak into every
    test that doesn't itself delenv, and MATCHING_MODE=hussain tests
    would then attempt a REAL network call. A test that specifically
    wants the "configured" path still sets fake values itself via
    monkeypatch.setenv within its own body, which composes correctly
    with — and simply overrides — the clearing done here first."""
    monkeypatch.delenv("RUNPOD_API_KEY", raising=False)
    monkeypatch.delenv("RUNPOD_ENDPOINT_ID", raising=False)
    # Same for the CV LLM settings: a developer's exported LLM_API_KEY
    # must never reach a test (or a fake server a test starts).
    for var in ("LLM_PROVIDER", "LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL", "LLM_TIMEOUT_SECONDS"):
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def test_engine():
    """A fresh in-memory SQLite database per test — fully isolated, never the
    real backend/futurepath.db file."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(test_engine) -> Session:
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(test_engine) -> TestClient:
    """TestClient wired to the isolated test_engine via a get_db override."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    def _override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
