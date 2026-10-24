"""POST /careers/match — the only matching route implemented in this
milestone. GET /careers/{role_id} is in the contract but out of scope here:
it needs Jawad's real role-detail/SDG/evidence data, which doesn't exist
yet, and is deferred to a future milestone rather than stubbed.

Each provider is its own Depends() so tests (or a future real integration)
can override just one — e.g. swap only get_matching_provider for Hussain's
real matcher without touching the DB or catalog wiring.

get_matching_provider is also imported by scenarios.py, roadmaps.py and
projects.py, so the ENABLE_FIXTURES gate below applies consistently to
every route that scores a role, from this one change.
"""
import os
import time

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.integration_errors import provider_unavailable
from app.core.time import utc_now_iso
from app.db.session import get_db
from app.schemas.matching import MatchRequest, MatchResponse, RoleMatch
from app.schemas.profile import DataMode
from app.services.hussain_matching.backend_adapter import DEGRADED_CAVEAT, HussainMatchingProvider
from app.services.interfaces import MatchingProvider, TrendProvider
from app.services.matching_provider import FixtureMatchingProvider
from app.services.matching_service import MatchingService
from app.services.profile_service import ProfileService
from app.services.role_catalog import FixtureRoleCatalog, RoleCatalogProvider
from app.services.role_catalog_cached import CachedCatalogError, CachedRoleCatalog, _load_json
from app.services.skill_not_equivalent_cached import load_skill_not_equivalent_pairs
from app.services.trend_provider import NullTrendProvider
from app.services.trend_signal_provider import CachedTrendSignalProvider

router = APIRouter()

# Milestone 10B: shared across requests (module/process lifetime), not
# per-request. get_matching_provider() is a Depends() factory called
# fresh on every HTTP request; constructing a new HussainMatchingProvider
# each time (Milestone 10A's behavior) reset its RunPod circuit-breaker
# (_down_until) on every single call, so a failed endpoint was retried on
# literally the very next request instead of actually cooling down for
# retry_after_seconds. Reusing one instance fixes that.
#
# Safe to share: HussainMatchingProvider never stores per-request student
# data — profile/roles/scenario/signals are passed as .match() arguments
# and never retained on self. Its only persisted state is the RunPod
# cooldown timer and a precomputed-embedding cache keyed by the skill
# catalogue's own shape (skill_id/name/aliases) — a function of Jawad's
# catalog data and RunPod reachability, never of any individual's
# profile. runpod_configured() is re-checked fresh on every .match() call
# (never cached on the instance), so adding, removing, or rotating
# RUNPOD_API_KEY/RUNPOD_ENDPOINT_ID takes effect on the very next call,
# once any in-progress cooldown has elapsed.
#
# Minor accepted risk: route handlers are sync `def`, so FastAPI runs
# them in a thread pool — concurrent requests could theoretically both
# observe "not cooling down" at the exact cooldown boundary and both
# attempt RunPod at once. That's a brief, harmless double-call, not a
# crash or data race on shared data; not worth a lock for this milestone.
#
# Milestone 10C addendum — credential rotation and bounded cache age:
# HussainMatchingProvider._providers caches a constructed
# RunPodEmbeddingProvider keyed only by the skill catalogue's own shape
# (skill_id/name/aliases) — NOT by RUNPOD_API_KEY/RUNPOD_ENDPOINT_ID. The
# cached provider's underlying _RunPodModel bakes the API key in at
# construction time. Without the check below, rotating or fixing
# RUNPOD_API_KEY while the process is running would silently keep using
# the OLD key forever (the cached provider is found and reused before
# runpod_configured()'s fresh os.environ read ever matters again) — a
# real, deployment-relevant bug this persistence otherwise introduces.
# Fix: track which credentials (and how long ago) the current shared
# instance was built with; rebuild it — a fresh HussainMatchingProvider,
# discarding its old embedding-client cache — whenever either changes.
# This also bounds how long any one skill-interpretation free-text query
# cache (EmbeddingProvider._query_vectors, keyed by the student's own
# typed skill text, kept in memory only) can live, instead of persisting
# for the entire process lifetime.
_shared_hussain_provider: HussainMatchingProvider | None = None
_shared_hussain_provider_credentials: tuple[str, str] | None = None
_shared_hussain_provider_catalog_mode: str | None = None
_shared_hussain_provider_created_at: float = 0.0
_SHARED_PROVIDER_MAX_AGE_SECONDS = 30 * 60  # 30 minutes — a deployment tuning choice, not a contract


def _current_runpod_credentials() -> tuple[str, str]:
    return (os.environ.get("RUNPOD_API_KEY", ""), os.environ.get("RUNPOD_ENDPOINT_ID", ""))


def _get_shared_hussain_provider(catalog_mode: str = "fixture") -> HussainMatchingProvider:
    """Milestone 13B-9: `catalog_mode` now also gates staleness —
    CATALOG_MODE=cached and CATALOG_MODE=fixture must never share one
    cached instance, because the skills_catalogue below is only valid
    for Jawad's real roles (see the real-data-only note further down).
    In production CATALOG_MODE is a fixed deployment setting that never
    changes mid-process, so this only matters for a test suite that
    exercises both values against the same shared global within one
    pytest session (e.g. test_matching_mode.py's full matrix)."""
    global _shared_hussain_provider, _shared_hussain_provider_credentials
    global _shared_hussain_provider_catalog_mode, _shared_hussain_provider_created_at
    now = time.monotonic()
    current_credentials = _current_runpod_credentials()
    stale = (
        _shared_hussain_provider is None
        or current_credentials != _shared_hussain_provider_credentials
        or catalog_mode != _shared_hussain_provider_catalog_mode
        or (now - _shared_hussain_provider_created_at) >= _SHARED_PROVIDER_MAX_AGE_SECONDS
    )
    if stale:
        # Milestone 13B-8: Jawad's skill_not_equivalent.json (optional —
        # [] if it hasn't landed yet) tells HussainMatchingProvider's
        # semantic-similarity path which skill pairs are related but NOT
        # interchangeable (e.g. python/javascript), so RunPod embeddings
        # never award partial credit for one when the other is required.
        # Never touches SkillNormalizer's exact/alias matching (a separate
        # code path) — an exact or aliased skill match is unaffected.
        # Harmless to pass unconditionally (even under CATALOG_MODE=
        # fixture): an inapplicable pair is just skipped with a warning
        # by HussainMatchingProvider._applicable_pairs(), never an error.
        try:
            not_equivalent = load_skill_not_equivalent_pairs()
        except CachedCatalogError as exc:
            raise provider_unavailable("MatchingProvider (hussain)", str(exc)) from exc

        # Milestone 13B-9: skills_catalogue is the real, full
        # app/data/cached/skills.json skill list (skill_id/name/aliases),
        # the same one cv_extraction_service.py already uses for CV
        # parsing. Without this, HussainMatchingProvider.catalogue_from_roles()
        # derives its catalogue purely from each role's required_skills
        # and always sets aliases=[] — so a CV alias like "QGIS"/"CAD"/
        # "Microsoft SQL Server" matched during CV upload would NOT be
        # recognized by exact-match catalogue matching here, only by
        # (optional, RunPod-dependent) semantic similarity.
        #
        # ONLY wired when CATALOG_MODE=cached (i.e. only alongside Jawad's
        # real roles): CATALOG_MODE=fixture's placeholder catalog
        # (app/services/role_catalog.py) has its own, unrelated fixture
        # skill_ids — one of them, literally "cad", collides with the
        # real catalog's new "CAD" alias for "cad_software" and makes
        # SkillNormalizer raise "Ambiguous alias" at construction time.
        # Fixture roles were never meant to share a skill namespace with
        # Jawad's real catalog, so this stays scoped to CATALOG_MODE=
        # cached rather than papering over that collision.
        skills_catalogue: list[dict] | None = None
        if catalog_mode == "cached":
            try:
                skills_catalogue = _load_json("skills.json")["skills"]
            except (OSError, ValueError, KeyError) as exc:
                raise provider_unavailable("MatchingProvider (hussain)", str(exc)) from exc

        _shared_hussain_provider = HussainMatchingProvider(
            result_model=RoleMatch, skills_catalogue=skills_catalogue, not_equivalent=not_equivalent
        )
        _shared_hussain_provider_credentials = current_credentials
        _shared_hussain_provider_catalog_mode = catalog_mode
        _shared_hussain_provider_created_at = now
    return _shared_hussain_provider


def reset_shared_hussain_provider_for_tests() -> None:
    """Test-only hook (see tests/conftest.py's autouse fixture): clears
    the module-level singleton above so each test starts with a fresh
    circuit-breaker state, undoing the cross-request sharing this module
    intentionally introduces for production. Never called from
    application code."""
    global _shared_hussain_provider, _shared_hussain_provider_credentials
    global _shared_hussain_provider_catalog_mode, _shared_hussain_provider_created_at
    _shared_hussain_provider = None
    _shared_hussain_provider_credentials = None
    _shared_hussain_provider_catalog_mode = None
    _shared_hussain_provider_created_at = 0.0


def matching_mode_warning(settings: Settings) -> str | None:
    """Passed into MatchingService so its warnings stay accurate. None
    preserves MatchingService's own default fixture-mode text (still
    correct for MATCHING_MODE=fixture).

    Milestone 10A: no longer claims semantic similarity is "explicitly
    disabled" — get_matching_provider() below no longer forces that.
    Whether RunPod is actually contacted on a given request depends on
    HussainMatchingProvider's own runpod_configured() check (both
    RUNPOD_API_KEY and RUNPOD_ENDPOINT_ID set) plus that endpoint's
    reachability; this text can only describe the possibility, since it
    is computed before matching runs. The per-match DEGRADED_CAVEAT is
    the authoritative, per-response signal for whether this request
    actually fell back.

    Milestone 13E-4: this text is student-facing, so it never names an
    internal env var (MATCHING_MODE=, RUNPOD_API_KEY, RUNPOD_ENDPOINT_ID),
    an implementation module path, or a teammate — only what a student
    needs: the algorithm runs offline by default, may use an external AI
    service when available, degrades visibly (the caveat text) when it
    can't, and the score is not a validated or hiring-predictive number."""
    if settings.MATCHING_MODE != "hussain":
        return None
    return (
        "Scores are produced by a deterministic skill-matching algorithm, "
        "run fully offline by default. Semantic skill similarity may use "
        "an external AI service (RunPod) when it is configured and "
        "reachable; if it isn't, matching automatically falls back to "
        "exact skill matching only, and each affected match is labelled "
        f"'{DEGRADED_CAVEAT}'. This methodology is an initial team choice, "
        "not a validated model, and the score is not a hiring probability."
    )


def get_matching_provider(settings: Settings = Depends(get_settings)) -> MatchingProvider:
    if settings.MATCHING_MODE == "hussain":
        # Hussain's provider itself needs no fixture data, but the roles
        # it would score do if CATALOG_MODE=fixture (the default) — that
        # IS fixture catalog data. ENABLE_FIXTURES=False must not let
        # that leak through silently; only CATALOG_MODE=cached makes this
        # combination genuinely fixture-free. Fail closed otherwise.
        if not settings.ENABLE_FIXTURES and settings.CATALOG_MODE != "cached":
            raise provider_unavailable(
                "MatchingProvider",
                "The deterministic matching algorithm is configured to require "
                "real, non-placeholder role data, but the active role catalogue "
                "is still a placeholder one. A real cached role catalogue must "
                "be configured to use this combination.",
            )
        # Milestone 10A: similarity is left unset (None) deliberately —
        # HussainMatchingProvider's own _semantic_similarity() decides per
        # request, calling RunPod only when runpod_configured() is true
        # (both RUNPOD_API_KEY and RUNPOD_ENDPOINT_ID set), and degrading
        # safely to exact-skill-only matching (DEGRADED_CAVEAT on every
        # affected match) if they're absent or the endpoint call fails.
        # Never guessed or forced either way from here.
        # Milestone 10B: the shared, process-lifetime instance (see
        # module-level comment above) — not a fresh one per request, so
        # its RunPod circuit-breaker actually persists across requests.
        return _get_shared_hussain_provider(settings.CATALOG_MODE)

    # ENABLE_FIXTURES=False signals "I expect real inference." No real
    # MatchingProvider implementation exists yet (Hussain's), so that case
    # must fail loudly rather than silently returning fixture scores
    # dressed up as something else. Independent of CATALOG_MODE below —
    # one gates the scoring provider, the other the role/skill data.
    if not settings.ENABLE_FIXTURES:
        raise provider_unavailable(
            "MatchingProvider",
            "ENABLE_FIXTURES is false and no real matching provider is implemented yet.",
        )
    return FixtureMatchingProvider()


def get_role_catalog(settings: Settings = Depends(get_settings)) -> RoleCatalogProvider:
    if settings.CATALOG_MODE == "cached":
        catalog = CachedRoleCatalog()
        try:
            catalog.list_roles()  # validate now; never silently fall back to fixture on failure
        except CachedCatalogError as exc:
            raise provider_unavailable("RoleCatalogProvider (cached)", str(exc)) from exc
        return catalog
    return FixtureRoleCatalog()


def catalog_data_mode(settings: Settings) -> DataMode:
    """The envelope's data_mode for every route that depends on
    get_role_catalog(). Always "fixture" for every CATALOG_MODE/
    MATCHING_MODE combination supported today: even when CATALOG_MODE=
    cached supplies real, cached O*NET-derived role/skill identifiers
    (and, as of Milestone 6D-2D, genuinely real cached roadmap resources
    and recommended/simulated projects too — CachedResourceCatalog /
    CachedProjectCatalog, not the Fixture* classes this docstring named
    before that milestone), and even when MATCHING_MODE=hussain runs a
    real (if still unvalidated and "initial team choice") algorithm
    instead of the fixture one, the one thing every response here always
    shares is a match score — and that score is still either
    fixture-generated or an unvalidated heuristic, never a verified
    outcome. A single data_mode value can't mark a response "partly
    cached, partly fixture"; labelling the whole response "cached" would
    let the score itself masquerade as a cached/verified outcome
    (REHAN_BACKEND_INTEGRATION.md: "don't let dummy scores accidentally
    masquerade as real outcomes"). The cached role/skill/resource/project
    provenance and the active matching algorithm are both disclosed
    explicitly via catalog_provenance_warnings()/matching_mode_warning()
    (and roadmaps.py/projects.py's own resource_provenance_warnings()/
    project_provenance_warnings()) instead of via this enum value.

    Milestone (Jawad fix, 2026-10-25): the live deployed app's frontend
    renders data_mode="fixture" as a generic "Demo data" badge
    ("Example data bundled with the prototype, not live") for every
    route, including this one — accurate for the score, but misleading
    about the role/skill/resource/project data underneath it when
    CATALOG_MODE=cached, which is real and sourced, not example data.
    This is a frontend labelling gap, not a bug in this function or in
    the underlying data; the fix belongs in the frontend's
    DataModeBadge component (components/data-mode-badge.tsx), not here.
    """
    return "fixture"


def catalog_provenance_warnings(settings: Settings) -> list[str]:
    """Scoped to role/skill catalog + scoring provenance only — always
    accurate for careers/scenarios (which have no resources/projects of
    their own). roadmaps.py/projects.py layer their own, separate
    resource_provenance_warnings()/project_provenance_warnings() instead
    of this function claiming anything about content it doesn't return,
    since that content is no longer always a fixture placeholder once
    CachedResourceCatalog/CachedProjectCatalog are selected (Milestone
    6D-2D).

    Milestone 13E-4: student-facing, so this never names the env var
    (CATALOG_MODE=), a teammate, an internal class name
    (FixtureMatchingProvider), or the internal data_mode enum value —
    only that the catalog is real (not invented placeholder data) and
    which kind of algorithm actually produced the score, in plain terms."""
    if settings.CATALOG_MODE != "cached":
        return []
    scoring_description = (
        "a deterministic skill-matching algorithm (semantic skill "
        "similarity optionally via an external AI service, falling back "
        "to exact skill matching if that isn't configured or reachable)"
        if settings.MATCHING_MODE == "hussain"
        else "an illustrative, placeholder algorithm"
    )
    return [
        "The role and skill catalog behind this response comes from a "
        "real, cached occupational dataset — these role and skill "
        "identifiers are real, not fictional placeholders. Matching "
        f"scores are still calculated by {scoring_description}, which is "
        "not yet a validated, real-world outcome."
    ]


def trend_signal_provenance_warnings(settings: Settings) -> list[str]:
    """Milestone 10C: discloses that CATALOG_MODE=cached feeds real,
    dated trend signals into matching/scenarios — never claims this is
    hiring demand, and never claims every skill or role has a signal
    (Jawad's catalog covers 12 of 20 skills; the other 8 and any role
    whose required skills are all uncovered simply see no adjustment,
    which scenario_service.py's own warnings already disclose per
    response).

    Milestone 13E-4: student-facing, so this never names the env var
    (CATALOG_MODE=), a teammate, or the internal cache directory path —
    only the two things a student needs: the signal is dated/cached
    developer activity, not every skill has one, and it is never hiring
    demand."""
    if settings.CATALOG_MODE != "cached":
        return []
    return [
        "When a scenario is requested, skill weight adjustments use real, "
        "dated, cached GitHub developer-activity signals — not every "
        "skill has a covered signal, and this is developer-activity data, "
        "never a verified hiring-demand measurement."
    ]


def get_trend_provider(settings: Settings = Depends(get_settings)) -> TrendProvider:
    """Milestone 10C: CATALOG_MODE=cached feeds MatchingService Jawad's
    real cached GitHub-developer-activity trend signals (CachedTrendSignalProvider —
    a pure read of app/data/cached/trend_snapshots/, never a live GitHub
    call); CATALOG_MODE=fixture (the default) keeps NullTrendProvider
    (no signals), unchanged from before — consistent with every other
    "use Jawad's real cached data only under CATALOG_MODE=cached" gate in
    this file. CachedTrendSignalProvider never raises: missing/invalid
    snapshot data degrades to an empty signal list, which
    scenarios.py's skill_weight_adjustments() already handles as "no
    scenario change" with its own explicit warning."""
    if settings.CATALOG_MODE == "cached":
        return CachedTrendSignalProvider()
    return NullTrendProvider()


def get_matching_service(
    db: Session = Depends(get_db),
    matcher: MatchingProvider = Depends(get_matching_provider),
    catalog: RoleCatalogProvider = Depends(get_role_catalog),
    trends: TrendProvider = Depends(get_trend_provider),
    settings: Settings = Depends(get_settings),
) -> MatchingService:
    return MatchingService(
        profile_service=ProfileService(db),
        catalog=catalog,
        matcher=matcher,
        trends=trends,
        matching_mode_warning=matching_mode_warning(settings),
    )


@router.post("/careers/match", response_model=MatchResponse)
def match_careers(
    payload: MatchRequest,
    service: MatchingService = Depends(get_matching_service),
    settings: Settings = Depends(get_settings),
) -> MatchResponse:
    outcome = service.match(payload)

    return MatchResponse(
        data=outcome.payload,
        data_mode=catalog_data_mode(settings),
        generated_at=utc_now_iso(),
        warnings=outcome.warnings + catalog_provenance_warnings(settings) + trend_signal_provenance_warnings(settings),
    )
