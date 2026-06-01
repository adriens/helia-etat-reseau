"""Couche SQLite — persistance et archivage des maintenances Helia NC."""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(
    __import__("os").environ.get("HELIA_DB_PATH", "/data/helia.db")
)


def _conn(path: Path = DB_PATH, *, readonly: bool = False) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    uri = f"file:{path}{'?mode=ro' if readonly else ''}";
    conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


@contextmanager
def get_db(readonly: bool = False):
    conn = _conn(readonly=readonly)
    try:
        yield conn
        if not readonly:
            conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Crée le schéma si besoin."""
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS scrape_runs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                scraped_at  TEXT    NOT NULL,
                nb_items    INTEGER NOT NULL,
                status      TEXT    NOT NULL DEFAULT 'ok',
                error       TEXT
            );

            CREATE TABLE IF NOT EXISTS maintenances (
                hash_id                     TEXT NOT NULL,
                scraped_at                  TEXT NOT NULL,
                source_url                  TEXT NOT NULL,
                timestamp_debut             TEXT NOT NULL,
                timestamp_fin               TEXT NOT NULL,
                duree_fenetre_minutes       INTEGER NOT NULL,
                duree_coupure_min_minutes   INTEGER,
                duree_coupure_max_minutes   INTEGER,
                communes_concernees         TEXT NOT NULL,   -- JSON array
                services                    TEXT NOT NULL,   -- JSON array
                impact                      TEXT NOT NULL,
                nb_communes_concernees      INTEGER NOT NULL,
                est_toute_nc                INTEGER NOT NULL,
                provinces_concernees        TEXT NOT NULL,   -- JSON array
                run_id                      INTEGER REFERENCES scrape_runs(id),
                PRIMARY KEY (hash_id, scraped_at)
            );

            CREATE INDEX IF NOT EXISTS idx_maint_hash ON maintenances(hash_id);
            CREATE INDEX IF NOT EXISTS idx_maint_debut ON maintenances(timestamp_debut);
        """)


def upsert_run(maintenances: list, scraped_at: str | None = None, error: str | None = None) -> int:
    """Insère un scrape run et les maintenances associées. Retourne le run_id."""
    ts = scraped_at or datetime.now(timezone.utc).isoformat()
    status = "error" if error else "ok"
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO scrape_runs (scraped_at, nb_items, status, error) VALUES (?, ?, ?, ?)",
            (ts, len(maintenances), status, error),
        )
        run_id = cur.lastrowid
        conn.executemany(
            """INSERT OR IGNORE INTO maintenances VALUES (
                :hash_id, :scraped_at, :source_url,
                :timestamp_debut, :timestamp_fin,
                :duree_fenetre_minutes, :duree_coupure_min_minutes, :duree_coupure_max_minutes,
                :communes_concernees, :services, :impact,
                :nb_communes_concernees, :est_toute_nc, :provinces_concernees,
                :run_id
            )""",
            [
                {
                    "hash_id": m["id"],
                    "scraped_at": m["scraped_at"],
                    "source_url": m["source_url"],
                    "timestamp_debut": m["timestamp_debut"],
                    "timestamp_fin": m["timestamp_fin"],
                    "duree_fenetre_minutes": m["duree_fenetre_minutes"],
                    "duree_coupure_min_minutes": m["duree_coupure_min_minutes"],
                    "duree_coupure_max_minutes": m["duree_coupure_max_minutes"],
                    "communes_concernees": json.dumps(m["communes_concernees"], ensure_ascii=False),
                    "services": json.dumps(m["services"], ensure_ascii=False),
                    "impact": m["impact"],
                    "nb_communes_concernees": m["nb_communes_concernees"],
                    "est_toute_nc": int(m["est_toute_nc"]),
                    "provinces_concernees": json.dumps(m["provinces_concernees"], ensure_ascii=False),
                    "run_id": run_id,
                }
                for m in maintenances
            ],
        )
    return run_id


def _row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    d["id"] = d.pop("hash_id")
    d["est_toute_nc"] = bool(d["est_toute_nc"])
    for field in ("communes_concernees", "services", "provinces_concernees"):
        d[field] = json.loads(d[field])
    return d


def get_latest_maintenances(
    commune: str | None = None,
    province: str | None = None,
    service: str | None = None,
) -> list[dict]:
    """Retourne les maintenances du dernier scrape réussi."""
    with get_db(readonly=True) as conn:
        row = conn.execute(
            "SELECT id FROM scrape_runs WHERE status='ok' ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if not row:
            return []
        run_id = row["id"]
        rows = conn.execute(
            "SELECT * FROM maintenances WHERE run_id = ? ORDER BY timestamp_debut",
            (run_id,),
        ).fetchall()
    items = [_row_to_dict(r) for r in rows]
    if commune:
        c = commune.upper()
        items = [m for m in items if c in m["communes_concernees"]]
    if province:
        items = [m for m in items if province in m["provinces_concernees"]]
    if service:
        items = [m for m in items if service in m["services"]]
    return items


def get_maintenance_by_id_db(hash_id: str) -> dict | None:
    """Dernière occurrence connue d'une maintenance par son hash."""
    with get_db(readonly=True) as conn:
        row = conn.execute(
            "SELECT * FROM maintenances WHERE hash_id = ? ORDER BY scraped_at DESC LIMIT 1",
            (hash_id,),
        ).fetchone()
    return _row_to_dict(row) if row else None


def get_scrape_runs(limit: int = 50) -> list[dict]:
    with get_db(readonly=True) as conn:
        rows = conn.execute(
            "SELECT * FROM scrape_runs ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]
