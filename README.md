# helia-etat-reseaux

SDK Python pour scraper les maintenances programmées du réseau télécoms Helia / OPT-NC depuis [helia.nc/etat-du-reseau](https://helia.nc/etat-du-reseau).

[![CI](https://github.com/adriens/helia-etat-reseau/actions/workflows/ci.yml/badge.svg)](https://github.com/adriens/helia-etat-reseau/actions/workflows/ci.yml)
[![Scraper](https://github.com/adriens/helia-etat-reseau/actions/workflows/nightly.yml/badge.svg)](https://github.com/adriens/helia-etat-reseau/actions/workflows/nightly.yml)
[![License: LGPL v3](https://img.shields.io/badge/License-LGPL_v3-blue.svg)](LICENSE)

## Installation

```bash
pip install helia-etat-reseaux
```

## Usage — SDK

```python
from helia_etat_reseaux import scrape_maintenances

maintenances = scrape_maintenances()

for m in maintenances:
    print(m.timestamp_debut, m.communes_concernees, m.impact)
```

Chaque objet `Maintenance` expose :

| Champ | Type | Description |
|---|---|---|
| `id` | `str` | Identifiant SHA256 stable (8 hex) |
| `timestamp_debut` / `timestamp_fin` | `str` ISO 8601 | Fenêtre de maintenance (UTC+11) |
| `communes_concernees` | `list[str]` | Communes officielles NC affectées |
| `provinces_concernees` | `list[Province]` | Provinces dérivées automatiquement |
| `services` | `list[Service]` | Services télécoms impactés |
| `impact` | `Impact` | Sévérité estimée de la coupure |
| `est_toute_nc` | `bool` | `True` si toute la NC est concernée |

## Usage — CLI

```bash
helia-etat-reseaux   # écrit les maintenances dans messages/*.json
```

## Structure

```
helia_etat_reseaux/
├── models.py      # Pydantic : Maintenance, Service, Impact, Province
├── scraper.py     # Scraping + parsing HTML helia.nc
├── geo.py         # Recherche géographique par rayon (communes NC)
├── db.py          # Persistance SQLite (optionnelle)
├── mcp.py         # Serveur MCP (intégration LLM)
└── scheduler.py   # Scheduler APScheduler (scrape périodique)
api/               # API FastAPI (mode conteneur)
webapp/            # Frontend Astro (calendrier + RSS)
```

## CI

- **Sur chaque PR** : lint Ruff + tests unitaires (couverture ≥ 70%)
- **Toutes les 6h** : tests d'intégration contre helia.nc — issue GitHub auto-créée en cas d'échec
- **Sur chaque tag `v*`** : release GitHub générée automatiquement depuis les PRs mergées

## Licence

[LGPL-3.0-or-later](LICENSE)
