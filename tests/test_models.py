"""Tests unitaires — modèles Pydantic."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from helia_etat_reseaux.models import Impact, Maintenance, Province, Service

VALID = dict(
    id="a6cec665",
    scraped_at=datetime.now(UTC).isoformat(),
    source_url="https://helia.nc/etat-du-reseau",
    timestamp_debut="2026-06-04T23:00:00+11:00",
    timestamp_fin="2026-06-05T05:00:00+11:00",
    duree_fenetre_minutes=360,
    duree_coupure_min_minutes=20,
    duree_coupure_max_minutes=30,
    communes_concernees=["NOUMEA"],
    services=["TELEPHONIE_FIXE"],
    impact="COUPURE_20_30_MIN",
    nb_communes_concernees=1,
    est_toute_nc=False,
    provinces_concernees=["PROVINCE_SUD"],
)


class TestMaintenanceValid:
    def test_nominal(self):
        m = Maintenance.model_validate(VALID)
        assert m.id == "a6cec665"
        assert m.impact == Impact.COUPURE_20_30_MIN
        assert Service.TELEPHONIE_FIXE in m.services
        assert Province.PROVINCE_SUD in m.provinces_concernees

    def test_null_coupure(self):
        data = {
            **VALID,
            "duree_coupure_min_minutes": None,
            "duree_coupure_max_minutes": None,
            "impact": "A_DETERMINER",
        }
        m = Maintenance.model_validate(data)
        assert m.duree_coupure_min_minutes is None

    def test_toute_nc(self):
        from helia_etat_reseaux.models import COMMUNES_OFFICIELLES

        data = {
            **VALID,
            "communes_concernees": sorted(COMMUNES_OFFICIELLES),
            "nb_communes_concernees": 33,
            "est_toute_nc": True,
            "provinces_concernees": ["PROVINCE_SUD", "PROVINCE_NORD", "ILES_LOYAUTE"],
        }
        m = Maintenance.model_validate(data)
        assert m.est_toute_nc is True


class TestMaintenanceInvalid:
    def test_id_wrong_format(self):
        with pytest.raises(ValidationError):
            Maintenance.model_validate({**VALID, "id": "ZZZZZZZZ"})

    def test_id_too_short(self):
        with pytest.raises(ValidationError):
            Maintenance.model_validate({**VALID, "id": "a6ce"})

    def test_empty_communes(self):
        with pytest.raises(ValidationError):
            Maintenance.model_validate({**VALID, "communes_concernees": []})

    def test_empty_services(self):
        with pytest.raises(ValidationError):
            Maintenance.model_validate({**VALID, "services": []})

    def test_negative_duree(self):
        with pytest.raises(ValidationError):
            Maintenance.model_validate({**VALID, "duree_fenetre_minutes": -1})

    def test_coupure_incoherence(self):
        """min > max doit lever une ValidationError."""
        with pytest.raises(ValidationError):
            Maintenance.model_validate(
                {
                    **VALID,
                    "duree_coupure_min_minutes": 30,
                    "duree_coupure_max_minutes": 10,
                }
            )

    def test_timestamp_order(self):
        """debut > fin doit lever une ValidationError."""
        with pytest.raises(ValidationError):
            Maintenance.model_validate(
                {
                    **VALID,
                    "timestamp_debut": "2026-06-05T05:00:00+11:00",
                    "timestamp_fin": "2026-06-04T23:00:00+11:00",
                }
            )


class TestEnums:
    def test_all_services_defined(self):
        expected = {
            "TELEPHONIE_FIXE",
            "TELEPHONIE_MOBILE",
            "INTERNET_FIXE",
            "INTERNET_MOBILE",
            "RESEAU_CUIVRE",
            "FIBRE_OPTIQUE",
            "LIAISONS_CELERIS_ETHERNET",
        }
        assert {s.value for s in Service} >= expected

    def test_all_provinces_defined(self):
        assert {p.value for p in Province} == {"PROVINCE_SUD", "PROVINCE_NORD", "ILES_LOYAUTE"}

    def test_all_impacts_defined(self):
        assert {i.value for i in Impact} == {"COUPURE_20_30_MIN", "COUPURE_30_MIN", "A_DETERMINER"}
