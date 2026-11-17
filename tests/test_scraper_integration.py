"""Tests d'intégration — réseau réel. Exécutés uniquement avec --run-integration."""

import logging

import pytest

from helia_etat_reseaux import scrape_maintenances
from helia_etat_reseaux.models import COMMUNES_OFFICIELLES


@pytest.mark.integration
class TestScraperLive:
    def test_scrape_returns_results(self):
        """Le scraper doit renvoyer au moins une maintenance depuis helia.nc."""
        items = scrape_maintenances()
        assert isinstance(items, list)
        # La page peut légitimement être vide (aucune maintenance planifiée)
        # mais le scraper ne doit pas lever d'exception

    @pytest.mark.integration
    def test_communes_are_official(self):
        for m in scrape_maintenances():
            for c in m.communes_concernees:
                assert c in COMMUNES_OFFICIELLES, (
                    f"Commune inconnue {c!r} — mapping ZONE_TO_COMMUNE à mettre à jour ?"
                )

    @pytest.mark.integration
    def test_ids_unique(self):
        items = scrape_maintenances()
        ids = [m.id for m in items]
        assert len(ids) == len(set(ids))

    @pytest.mark.integration
    def test_stable_ids(self):
        """Deux scrapes consécutifs sur la même page → mêmes ids."""
        first = {m.id for m in scrape_maintenances()}
        second = {m.id for m in scrape_maintenances()}
        assert first == second, (
            f"IDs instables — apparus : {second - first}, disparus : {first - second}"
        )

    @pytest.mark.integration
    def test_no_unknown_zones(self):
        """Aucune zone brute ne doit être inconnue du mapping ZONE_TO_COMMUNE."""
        unknowns = [
            (m.id, m.zones_non_reconnues) for m in scrape_maintenances() if m.zones_non_reconnues
        ]
        assert not unknowns, (
            "Zones inconnues détectées — mettre à jour ZONE_TO_COMMUNE dans scraper.py :\n"
            + "\n".join(f"  [{mid}] {zones}" for mid, zones in unknowns)
        )

    @pytest.mark.integration
    def test_no_skipped_items(self, caplog):
        """Aucun item de la page ne doit être ignoré faute de parsing (zone ou service)."""
        with caplog.at_level(logging.WARNING, logger="helia_etat_reseaux.scraper"):
            scrape_maintenances()
        skipped = [r.getMessage() for r in caplog.records if "Item ignoré" in r.getMessage()]
        assert not skipped, "Items ignorés au parsing :\n" + "\n".join(
            f"  {msg}" for msg in skipped
        )
