from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["infra"])


class HealthResponse(BaseModel):
    status: str
    version: str


class CacheStats(BaseModel):
    size: int
    maxsize: int
    ttl_seconds: int
    currsize: int


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Healthcheck",
    description="Endpoint de liveness utilisé par Docker et Kubernetes.",
    include_in_schema=True,
)
def health() -> HealthResponse:
    return HealthResponse(status="ok", version="0.2.0")


@router.get(
    "/cache/stats",
    response_model=CacheStats,
    summary="Statistiques du cache TTL",
    description=(
        "Retourne l'état du cache mémoire TTL utilisé pour les lookups par `id`. "
        "TTL configurable via `HELIA_CACHE_TTL_SECONDS` (défaut : 300 s)."
    ),
)
def cache_stats_endpoint() -> CacheStats:
    from api.cache import stats

    return CacheStats(**stats())
