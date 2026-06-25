"""Tests unitaires du scraper — offline, fixture HTML statique."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from helia_etat_reseaux.models import COMMUNES_OFFICIELLES, Impact, Province, Service
from helia_etat_reseaux.scraper import (
    _parse_date_range,
    _split_zones,
    _to_iso,
    _zones_to_communes,
    parse_items,
    scrape_maintenances,
)

# ── _split_zones ──────────────────────────────────────────────────────────────


class TestSplitZones:
    def test_single(self):
        assert _split_zones("NOUMEA") == ["NOUMEA"]

    def test_comma(self):
        assert _split_zones("NOUMEA, DUMBEA") == ["NOUMEA", "DUMBEA"]

    def test_et_separator(self):
        assert _split_zones("NOUMEA et DUMBEA") == ["NOUMEA", "DUMBEA"]

    def test_comma_and_et_mixed(self):
        result = _split_zones("NOUMEA, DUMBEA et PAITA")
        assert result == ["NOUMEA", "DUMBEA", "PAITA"]

    def test_parentheses_not_split(self):
        """La virgule dans les parenthèses ne doit PAS créer de split."""
        result = _split_zones("Nouméa (Val Plaisance, Anse-Vata), Dumbea")
        assert len(result) == 2
        assert any("Val Plaisance" in z for z in result)
        assert any("Dumbea" in z for z in result)

    def test_strips_whitespace(self):
        result = _split_zones("  NOUMEA  ,  DUMBEA  ")
        assert result == ["NOUMEA", "DUMBEA"]

    def test_nbsp_normalized(self):
        result = _split_zones("NOUMEA\xa0, DUMBEA")
        assert result == ["NOUMEA", "DUMBEA"]


# ── _zones_to_communes ────────────────────────────────────────────────────────


class TestZonesToCommunes:
    def test_exact_match(self):
        communes, unknown = _zones_to_communes(["Koutio"])
        assert communes == ["DUMBEA"]
        assert unknown == []

    def test_parenthetical_suffix_stripped(self):
        """Un suffixe parenthésé (rue/tribu) ne doit pas empêcher la reconnaissance."""
        communes, unknown = _zones_to_communes(["Koutio (Rue Becquerel)"])
        assert communes == ["DUMBEA"]
        assert unknown == []

    def test_parenthetical_commune(self):
        communes, unknown = _zones_to_communes(["La Foa (Pocquereux)"])
        assert communes == ["LA FOA"]
        assert unknown == []

    def test_apogotti_variant(self):
        """Variante orthographique 'Apogotti' (deux t) reconnue comme Dumbéa."""
        communes, unknown = _zones_to_communes(["Apogotti"])
        assert communes == ["DUMBEA"]
        assert unknown == []

    def test_genuinely_unknown_zone(self):
        communes, unknown = _zones_to_communes(["ZoneInexistante"])
        assert communes == []
        assert unknown == ["ZoneInexistante"]


# ── _parse_date_range ─────────────────────────────────────────────────────────


class TestParseDateRange:
    def test_single_day(self):
        assert _parse_date_range("16 juillet 2026") == (date(2026, 7, 16), date(2026, 7, 16))

    def test_au_range(self):
        assert _parse_date_range("2 au 4 juillet 2026") == (date(2026, 7, 2), date(2026, 7, 4))

    def test_dash_list(self):
        """Liste de jours '7-8-9 juillet 2026' -> plage du 1er au dernier."""
        assert _parse_date_range("7-8-9 juillet 2026") == (date(2026, 7, 7), date(2026, 7, 9))

    def test_dash_pair(self):
        assert _parse_date_range("7-8 juillet 2026") == (date(2026, 7, 7), date(2026, 7, 8))

    def test_unparseable_raises(self):
        with pytest.raises(ValueError, match="Date non parseable"):
            _parse_date_range("la semaine prochaine")


# ── _to_iso ───────────────────────────────────────────────────────────────────


class TestToIso:
    def test_format(self):
        result = _to_iso(date(2026, 6, 4), 23, 0)
        assert result == "2026-06-04T23:00:00+11:00"

    def test_midnight(self):
        result = _to_iso(date(2026, 6, 4), 0, 0)
        assert result == "2026-06-04T00:00:00+11:00"

    def test_padding(self):
        result = _to_iso(date(2026, 1, 1), 5, 5)
        assert result == "2026-01-01T05:05:00+11:00"

    def test_timezone_suffix(self):
        assert _to_iso(date(2026, 6, 1), 12, 30).endswith("+11:00")


# ── parse_items ───────────────────────────────────────────────────────────────


class TestParseItems:
    def test_returns_list(self, fixture_html):
        items = parse_items(fixture_html)
        assert isinstance(items, list)

    def test_not_empty(self, fixture_html):
        items = parse_items(fixture_html)
        assert len(items) > 0, "Aucune maintenance parsée depuis la fixture"

    def test_required_keys(self, fixture_html):
        for item in parse_items(fixture_html):
            assert "date" in item
            assert "Créneau d'intervention" in item
            assert "Zone concernée" in item
            assert "Impacts" in item

    def test_date_non_empty(self, fixture_html):
        for item in parse_items(fixture_html):
            assert item["date"].strip()

    def test_zone_non_empty(self, fixture_html):
        for item in parse_items(fixture_html):
            assert item["Zone concernée"].strip()


# ── scrape_maintenances (avec mock HTTP) ──────────────────────────────────────


class TestScrapeMaintenancesMocked:
    def test_returns_maintenance_objects(self, fixture_html):
        mock_resp = MagicMock()
        mock_resp.text = fixture_html
        mock_resp.raise_for_status = MagicMock()

        with patch("helia_etat_reseaux.scraper.requests.get", return_value=mock_resp):
            items = scrape_maintenances()

        assert isinstance(items, list)
        assert len(items) > 0

    def test_ids_are_unique(self, fixture_html):
        mock_resp = MagicMock()
        mock_resp.text = fixture_html
        mock_resp.raise_for_status = MagicMock()

        with patch("helia_etat_reseaux.scraper.requests.get", return_value=mock_resp):
            items = scrape_maintenances()

        ids = [m.id for m in items]
        assert len(ids) == len(set(ids)), "Des id dupliqués ont été générés"

    def test_id_format(self, fixture_html):
        mock_resp = MagicMock()
        mock_resp.text = fixture_html
        mock_resp.raise_for_status = MagicMock()

        with patch("helia_etat_reseaux.scraper.requests.get", return_value=mock_resp):
            items = scrape_maintenances()

        import re

        for m in items:
            assert re.match(r"^[0-9a-f]{8}$", m.id), f"id invalide : {m.id!r}"

    def test_communes_are_official(self, fixture_html):
        mock_resp = MagicMock()
        mock_resp.text = fixture_html
        mock_resp.raise_for_status = MagicMock()

        with patch("helia_etat_reseaux.scraper.requests.get", return_value=mock_resp):
            items = scrape_maintenances()

        for m in items:
            for c in m.communes_concernees:
                assert c in COMMUNES_OFFICIELLES, (
                    f"Commune non officielle {c!r} dans la maintenance {m.id}"
                )

    def test_timestamps_order(self, fixture_html):
        mock_resp = MagicMock()
        mock_resp.text = fixture_html
        mock_resp.raise_for_status = MagicMock()

        with patch("helia_etat_reseaux.scraper.requests.get", return_value=mock_resp):
            items = scrape_maintenances()

        for m in items:
            assert m.timestamp_debut <= m.timestamp_fin, f"début > fin pour {m.id}"

    def test_services_enum(self, fixture_html):
        mock_resp = MagicMock()
        mock_resp.text = fixture_html
        mock_resp.raise_for_status = MagicMock()

        with patch("helia_etat_reseaux.scraper.requests.get", return_value=mock_resp):
            items = scrape_maintenances()

        for m in items:
            for s in m.services:
                assert isinstance(s, Service)

    def test_impact_enum(self, fixture_html):
        mock_resp = MagicMock()
        mock_resp.text = fixture_html
        mock_resp.raise_for_status = MagicMock()

        with patch("helia_etat_reseaux.scraper.requests.get", return_value=mock_resp):
            items = scrape_maintenances()

        for m in items:
            assert isinstance(m.impact, Impact)

    def test_provinces_derived(self, fixture_html):
        mock_resp = MagicMock()
        mock_resp.text = fixture_html
        mock_resp.raise_for_status = MagicMock()

        with patch("helia_etat_reseaux.scraper.requests.get", return_value=mock_resp):
            items = scrape_maintenances()

        for m in items:
            assert len(m.provinces_concernees) >= 1
            for p in m.provinces_concernees:
                assert isinstance(p, Province)

    def test_est_toute_nc_coherence(self, fixture_html):
        mock_resp = MagicMock()
        mock_resp.text = fixture_html
        mock_resp.raise_for_status = MagicMock()

        with patch("helia_etat_reseaux.scraper.requests.get", return_value=mock_resp):
            items = scrape_maintenances()

        for m in items:
            if m.est_toute_nc:
                assert m.nb_communes_concernees == len(COMMUNES_OFFICIELLES)

    def test_http_error_raises_runtime(self):
        import requests as req

        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = req.exceptions.HTTPError("503")

        with (
            patch("helia_etat_reseaux.scraper.requests.get", return_value=mock_resp),
            pytest.raises(RuntimeError, match="3"),
        ):
            scrape_maintenances()

    def test_stable_id_between_scrapes(self, fixture_html):
        """Le même HTML doit produire les mêmes ids."""
        mock_resp = MagicMock()
        mock_resp.text = fixture_html
        mock_resp.raise_for_status = MagicMock()

        with patch("helia_etat_reseaux.scraper.requests.get", return_value=mock_resp):
            first = {m.id for m in scrape_maintenances()}
            second = {m.id for m in scrape_maintenances()}

        assert first == second, "Les ids ne sont pas stables entre deux scrapes du même HTML"
