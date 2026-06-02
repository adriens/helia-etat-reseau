"""Sync Helia maintenance data between live site and the data repository.

Logic:
  - New IDs (scraped, not in active/)  → write to active/<id>.json
  - Gone IDs (in active/, not scraped) → move to archive/<year>/<id>.json
  - Unchanged IDs                      → no-op (preserves first-seen scraped_at)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from helia_etat_reseaux.scraper import scrape_maintenances


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True, type=Path)
    args = parser.parse_args()

    active_dir = args.data_dir / "active"
    archive_dir = args.data_dir / "archive"
    active_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)

    current = {m.id: m for m in scrape_maintenances()}
    existing = {f.stem: f for f in active_dir.glob("*.json")}

    added, archived = [], []

    for mid, m in current.items():
        if mid not in existing:
            (active_dir / f"{mid}.json").write_text(m.model_dump_json(indent=2))
            added.append(mid)

    for mid, fpath in existing.items():
        if mid not in current:
            data = json.loads(fpath.read_text())
            year = data["timestamp_debut"][:4]
            year_dir = archive_dir / year
            year_dir.mkdir(parents=True, exist_ok=True)
            fpath.rename(year_dir / fpath.name)
            archived.append(mid)

    print(f"active={len(current)}  +{len(added)} new  -{len(archived)} archived")


if __name__ == "__main__":
    main()
