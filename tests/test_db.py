"""Tests unitaires pour la couche SQLite (helia_etat_reseaux.db)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

import helia_etat_reseaux.db as db_module
from helia_etat_reseaux.db import (
    get_db,
    get_latest_maintenances,
    get_maintenance_by_id_db,
    get_scrape_runs,
    init_db,
    upsert_run,
)

_SAMPLE = {
    "id": "a6cec665",
    "scraped_at": "2026-06-01T10:00:00Z",
    "source_url": "https://helia.nc/etat-du-reseau",
    "timestamp_debut": "2026-06-01T23:00:00+11:00",
    "timestamp_fin": "2026-06-02T05:00:00+11:00",
    "duree_fenetre_minutes": 360,
    "duree_coupure_min_minutes": 20,
    "duree_coupure_max_minutes": 30,
    "communes_concernees": ["NOUMEA", "DUMBEA"],
    "services": ["TELEPHONIE_FIXE"],
    "impact": "COUPURE_20_30_MIN",
    "nb_communes_concernees": 2,
    "est_toute_nc": False,
    "provinces_concernees": ["PROVINCE_SUD"],
}


@pytest.fixture()
def tmp_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Base SQLite temporaire isolée par test."""
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    init_db()
    return db_path


class TestInitDb:
    def test_creates_tables(self, tmp_db):
        with get_db(readonly=True) as conn:
            tables = {
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
        assert {"scrape_runs", "maintenances"} <= tables


class TestUpsertRun:
    def test_inserts_run_and_maintenances(self, tmp_db):
        run_id = upsert_run([_SAMPLE], scraped_at="2026-06-01T10:00:00Z")
        assert run_id == 1

        with get_db(readonly=True) as conn:
            run = conn.execute("SELECT * FROM scrape_runs WHERE id=1").fetchone()
            assert run["nb_items"] == 1
            assert run["status"] == "ok"

            row = conn.execute("SELECT * FROM maintenances WHERE hash_id=?", ("a6cec665",)).fetchone()
            assert row is not None
            assert json.loads(row["communes_concernees"]) == ["NOUMEA", "DUMBEA"]

    def test_idempotent_on_duplicate(self, tmp_db):
        upsert_run([_SAMPLE])
        upsert_run([_SAMPLE])
        with get_db(readonly=True) as conn:
            count = conn.execute("SELECT COUNT(*) FROM maintenances").fetchone()[0]
        assert count == 1

    def test_error_run(self, tmp_db):
        run_id = upsert_run([], error="boom")
        with get_db(readonly=True) as conn:
            run = conn.execute("SELECT * FROM scrape_runs WHERE id=?", (run_id,)).fetchone()
        assert run["status"] == "error"
        assert run["error"] == "boom"


class TestGetLatestMaintenances:
    def test_returns_last_ok_run(self, tmp_db):
        upsert_run([_SAMPLE])
        items = get_latest_maintenances()
        assert len(items) == 1
        assert items[0]["id"] == "a6cec665"

    def test_returns_empty_when_no_runs(self, tmp_db):
        assert get_latest_maintenances() == []

    def test_filter_by_commune(self, tmp_db):
        upsert_run([_SAMPLE])
        assert len(get_latest_maintenances(commune="NOUMEA")) == 1
        assert get_latest_maintenances(commune="LIFOU") == []

    def test_filter_by_province(self, tmp_db):
        upsert_run([_SAMPLE])
        assert len(get_latest_maintenances(province="PROVINCE_SUD")) == 1
        assert get_latest_maintenances(province="PROVINCE_NORD") == []

    def test_filter_by_service(self, tmp_db):
        upsert_run([_SAMPLE])
        assert len(get_latest_maintenances(service="TELEPHONIE_FIXE")) == 1
        assert get_latest_maintenances(service="INTERNET_FIXE") == []

    def test_skips_error_runs(self, tmp_db):
        upsert_run([], error="boom")
        assert get_latest_maintenances() == []


class TestGetMaintenanceById:
    def test_found(self, tmp_db):
        upsert_run([_SAMPLE])
        item = get_maintenance_by_id_db("a6cec665")
        assert item is not None
        assert item["id"] == "a6cec665"
        assert item["est_toute_nc"] is False

    def test_not_found(self, tmp_db):
        assert get_maintenance_by_id_db("deadbeef") is None


class TestGetScrapeRuns:
    def test_returns_runs_desc(self, tmp_db):
        upsert_run([_SAMPLE])
        upsert_run([])
        runs = get_scrape_runs()
        assert len(runs) == 2
        assert runs[0]["id"] > runs[1]["id"]

    def test_limit(self, tmp_db):
        for _ in range(5):
            upsert_run([])
        assert len(get_scrape_runs(limit=3)) == 3
