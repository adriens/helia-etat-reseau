import os

from fastapi import APIRouter, HTTPException, Path, Query
from helia_etat_reseaux import Maintenance, Province, Service, scrape_maintenances
from helia_etat_reseaux.geo import communes_within_radius
from api.cache import get as cache_get, set as cache_set, stats as cache_stats

router = APIRouter(prefix="/maintenances", tags=["maintenances"])

_USE_DB = os.environ.get("HELIA_USE_DB", "0") == "1"

_503 = {
    "description": "La page helia.nc est inaccessible après 3 tentatives.",
    "content": {"application/json": {"example": {"detail": "Scrape échoué après 3 tentatives"}}},
}
_404 = {
    "description": "Aucune maintenance ne correspond.",
    "content": {"application/json": {"example": {"detail": "'deadbeef' introuvable"}}},
}


def _fetch(
    commune: str | None = None,
    province: Province | None = None,
    service: Service | None = None,
) -> list[dict]:
    if _USE_DB:
        from helia_etat_reseaux.db import get_latest_maintenances
        return get_latest_maintenances(
            commune=commune,
            province=province.value if province else None,
            service=service.value if service else None,
        )
    try:
        items = scrape_maintenances()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    result = [m.model_dump(mode="json") for m in items]
    if commune:
        c = commune.upper()
        result = [m for m in result if c in m["communes_concernees"]]
    if province:
        result = [m for m in result if province.value in m["provinces_concernees"]]
    if service:
        result = [m for m in result if service.value in m["services"]]
    return result


@router.get(
    "/",
    response_model=list[Maintenance],
    summary="Liste les maintenances programmées",
    description=(
        "Retourne la liste des maintenances, optionnellement filtrée par commune, province ou service.\n\n"
        "**Mode DB** (`HELIA_USE_DB=1`) : lit le dernier scrape archivé en SQLite.\n"
        "**Mode live** (défaut) : scrape en temps réel helia.nc."
    ),
    response_description="Maintenances filtrées et triées par ordre d'apparition sur la page.",
    responses={503: _503},
)
def get_maintenances(
    commune: str | None = Query(
        default=None,
        description="Filtre sur le nom officiel d'une commune (ex: `NOUMEA`). Insensible à la casse.",
    ),
    province: Province | None = Query(
        default=None,
        description="Filtre sur une province administrative NC.",
    ),
    service: Service | None = Query(
        default=None,
        description="Filtre sur un service télécom impacté.",
    ),
) -> list[Maintenance]:
    return [Maintenance.model_validate(m) for m in _fetch(commune, province, service)]


@router.get(
    "/search",
    response_model=list[Maintenance],
    summary="Recherche géographique par point et rayon",
    description=(
        "Retourne les maintenances affectant au moins une commune dont le centroide "
        "est dans le rayon fourni autour du point `lat`/`lon`.\n\n"
        "Utile pour : *«Quelles maintenances me concernent ?»* depuis la géolocalisation du navigateur."
    ),
    response_description="Maintenances géographiquement proches du point, ordonnées par date de début.",
    responses={503: _503},
)
def search_near(
    lat: float = Query(description="Latitude WGS84 (ex: `-22.27` pour Nouméa).", ge=-90, le=90),
    lon: float = Query(description="Longitude WGS84 (ex: `166.45` pour Nouméa).", ge=-180, le=180),
    radius_km: float = Query(
        default=50,
        description="Rayon de recherche en kilomètres.",
        gt=0,
        le=500,
    ),
) -> list[Maintenance]:
    nearby = set(communes_within_radius(lat, lon, radius_km))
    if not nearby:
        return []
    items = _fetch()
    return [Maintenance.model_validate(m) for m in items if set(m["communes_concernees"]) & nearby]


@router.get(
    "/{id}",
    response_model=Maintenance,
    summary="Récupère une maintenance par son identifiant SHA256",
    description=(
        "Retourne la maintenance dont l'`id` correspond aux 8 caractères hex fournis. "
        "L'`id` est stable tant que la maintenance n'est pas modifiée sur la source."
    ),
    response_description="La maintenance correspondant à l'identifiant.",
    responses={404: _404, 503: _503},
)
def get_maintenance_by_id(
    id: str = Path(
        pattern=r"^[0-9a-f]{8}$",
        description="Identifiant SHA256 de la maintenance (8 caractères hex minuscules).",
        examples=["a6cec665"],
    ),
) -> Maintenance:
    cache_key = f"maint:{id}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    if _USE_DB:
        from helia_etat_reseaux.db import get_maintenance_by_id_db
        m = get_maintenance_by_id_db(id)
        if m:
            result = Maintenance.model_validate(m)
            cache_set(cache_key, result)
            return result
        raise HTTPException(status_code=404, detail=f"{id!r} introuvable")

    for m in _fetch():
        if m["id"] == id:
            result = Maintenance.model_validate(m)
            cache_set(cache_key, result)
            return result
    raise HTTPException(status_code=404, detail=f"{id!r} introuvable")
