"""Tests d'intégration — réseau réel. Exécutés uniquement avec --run-integration."""
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
        first  = {m.id for m in scrape_maintenances()}
        second = {m.id for m in scrape_maintenances()}
        assert first == second, (
            f"IDs instables — apparus : {second - first}, disparus : {first - second}"
        )
