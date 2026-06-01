"""MCP server exposant les maintenances Helia NC comme outils."""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP
from helia_etat_reseaux import scrape_maintenances
from helia_etat_reseaux.geo import communes_within_radius

mcp = FastMCP(
    name="helia-nc-maintenances",
    instructions=(
        "Accès aux maintenances programmées du réseau Helia by OPT-NC en Nouvelle-Calédonie. "
        "Utilisez get_maintenances pour lister, get_maintenance_by_id pour une maintenance précise, "
        "search_by_commune pour filtrer par commune, et search_near pour une recherche géographique."
    ),
)


def _all() -> list[dict]:
    return [m.model_dump(mode="json") for m in scrape_maintenances()]


@mcp.tool()
def get_maintenances(
    commune: str | None = None,
    province: str | None = None,
    service: str | None = None,
) -> list[dict]:
    """Retourne la liste des maintenances programmées Helia NC.

    Filtres optionnels : commune (nom officiel, insensible à la casse),
    province (PROVINCE_SUD / PROVINCE_NORD / ILES_LOYAUTE), service
    (TELEPHONIE_FIXE / TELEPHONIE_MOBILE / INTERNET_FIXE / INTERNET_MOBILE / TELEVISION).
    """
    items = _all()
    if commune:
        c = commune.upper()
        items = [m for m in items if c in m["communes_concernees"]]
    if province:
        items = [m for m in items if province in m["provinces_concernees"]]
    if service:
        items = [m for m in items if service in m["services"]]
    return items


@mcp.tool()
def get_maintenance_by_id(id: str) -> dict | None:
    """Retourne une maintenance par son identifiant SHA256 (8 hex).

    Retourne None si l'identifiant n'existe pas dans le scrape courant.
    """
    for m in _all():
        if m["id"] == id:
            return m
    return None


@mcp.tool()
def search_by_commune(commune: str) -> list[dict]:
    """Retourne toutes les maintenances affectant la commune donnée.

    Le nom doit correspondre à un nom officiel NC (ex: NOUMEA, DUMBEA).
    """
    c = commune.upper()
    return [m for m in _all() if c in m["communes_concernees"]]


@mcp.tool()
def search_near(lat: float, lon: float, radius_km: float = 50.0) -> list[dict]:
    """Retourne les maintenances dont au moins une commune est dans le rayon donné.

    lat / lon : coordonnées WGS84 (ex: -22.27 / 166.45 pour Nouméa).
    radius_km : rayon en km (défaut 50, max 500).
    """
    radius_km = min(max(radius_km, 0.1), 500.0)
    nearby = set(communes_within_radius(lat, lon, radius_km))
    if not nearby:
        return []
    return [m for m in _all() if set(m["communes_concernees"]) & nearby]
