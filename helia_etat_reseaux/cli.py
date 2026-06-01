from __future__ import annotations

import json
import os
import sys

from .scraper import scrape_maintenances


def main() -> None:
    out_dir = "messages"
    if os.path.exists(out_dir):
        for old in os.listdir(out_dir):
            if old.endswith(".json"):
                os.remove(os.path.join(out_dir, old))
    os.makedirs(out_dir, exist_ok=True)

    try:
        maintenances = scrape_maintenances()
    except RuntimeError as exc:
        print(f"ERREUR : {exc}", file=sys.stderr)
        sys.exit(1)

    for m in maintenances:
        path = os.path.join(out_dir, f"{m.id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(m.model_dump(mode="json"), f, ensure_ascii=False, indent=2)

    print(f"{len(maintenances)} fichiers écrits dans {out_dir}/")
