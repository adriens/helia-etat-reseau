import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from prometheus_fastapi_instrumentator import Instrumentator

from helia_etat_reseaux.mcp import mcp

from .routes import health, maintenances
from .telemetry import setup_telemetry

DESCRIPTION = """
## Helia NC — Maintenances programmées

API de consultation des maintenances programmées sur le réseau télécoms
**Helia by OPT-NC** en Nouvelle-Calédonie.

### Source des données
Les données sont scrapées depuis [helia.nc/etat-du-reseau](https://helia.nc/etat-du-reseau)
et archivées en **SQLite** (WAL mode). Un job tourne **toutes les heures** pour maintenir
la base à jour. Chaque appel API lit le dernier scrape réussi — temps de réponse garanti,
même si helia.nc est temporairement inaccessible.

### Identifiants stables
Chaque maintenance possède un `id` SHA256 (8 hex) calculé sur ses champs métier.
Cet identifiant est **stable entre deux scrapes** si la maintenance n'a pas changé :
- clé de message **Kafka** (partitionnement déterministe)
- upsert idempotent dans **OpenSearch** (`_id`)

### Communes officielles
Normalisées selon [communes-nc-limites-terrestres-simplifiees](https://data.gouv.nc/explore/dataset/communes-nc-limites-terrestres-simplifiees/).
Jointure directe possible sur le champ `nom`.

### Recherche géographique
`GET /maintenances/search?lat=...&lon=...&radius_km=...` — trouvez les maintenances
qui vous concernent à partir de votre géolocalisation.

### Timezone
Timestamps de maintenance en **heure locale NC (UTC+11)**. `scraped_at` en **UTC**.

### MCP
Serveur MCP monté sur `/mcp` (transport HTTP streamable) — compatible Claude Desktop
et `claude` CLI. Outils : `get_maintenances`, `get_maintenance_by_id`,
`search_by_commune`, `search_near`.
"""

_USE_DB = os.environ.get("HELIA_USE_DB", "0") == "1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    if _USE_DB:
        from helia_etat_reseaux.scheduler import start_scheduler, stop_scheduler

        start_scheduler()
        yield
        stop_scheduler()
    else:
        yield


app = FastAPI(
    title="Helia NC — État du réseau",
    description=DESCRIPTION,
    version="0.2.0",
    contact={"name": "OPT-NC", "url": "https://www.opt.nc"},
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "maintenances",
            "description": "Consultation et recherche des maintenances programmées Helia NC.",
        },
        {
            "name": "infra",
            "description": "Endpoints opérationnels (healthcheck, scrape runs).",
        },
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(maintenances.router)

# Prometheus metrics at /metrics — scrape-able by Prometheus / Grafana
Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    excluded_handlers=["/metrics", "/health"],
).instrument(app).expose(app, tags=["infra"])

# MCP server mounted at /mcp — streamable HTTP transport (compatible Claude Desktop, claude CLI)
app.mount("/mcp", mcp.streamable_http_app())


setup_telemetry(app)


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/redoc")
