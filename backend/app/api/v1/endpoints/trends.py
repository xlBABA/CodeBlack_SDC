"""GET /trends — the only trend retrieval route in contracts/API_CONTRACT.md.

Stateless: no profile/DB dependency. `data_mode` is always "fixture" since
no real trend pipeline (Jawad's services/trends/**) is wired in yet.
"""
from fastapi import APIRouter, Depends, Query

from app.core.time import utc_now_iso
from app.schemas.trends import TrendsPayload, TrendsResponse
from app.services.interfaces import TrendProvider
from app.services.trend_provider import FixtureTrendProvider

router = APIRouter()


def get_trend_provider() -> TrendProvider:
    return FixtureTrendProvider()


@router.get("/trends", response_model=TrendsResponse)
def get_trends(
    role_id: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1),
    provider: TrendProvider = Depends(get_trend_provider),
) -> TrendsResponse:
    result = provider.latest(role_id=role_id)
    signals = result.signals[:limit]

    payload = TrendsPayload(
        signals=signals,
        last_successful_refresh_at=result.last_successful_refresh_at,
        source_status=result.source_status,
    )
    warnings = [
        "No real trend source is connected yet; any signals shown are "
        "synthetic, clearly-labeled hypothetical placeholders demonstrating "
        "the contract shape, not sourced evidence or live job-market data."
    ]

    return TrendsResponse(
        data=payload,
        data_mode="fixture",
        generated_at=utc_now_iso(),
        warnings=warnings,
    )
