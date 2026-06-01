"""Tests unitaires — geo.py."""
from helia_etat_reseaux.geo import COMMUNE_CENTROIDS, communes_within_radius, haversine_km


class TestHaversine:
    def test_same_point(self):
        assert haversine_km(0, 0, 0, 0) == 0.0

    def test_known_distance(self):
        # Nouméa → Dumbéa ≈ 16 km à vol d'oiseau
        lat1, lon1 = COMMUNE_CENTROIDS["NOUMEA"]
        lat2, lon2 = COMMUNE_CENTROIDS["DUMBEA"]
        d = haversine_km(lat1, lon1, lat2, lon2)
        assert 10 < d < 25, f"Distance Nouméa-Dumbéa inattendue : {d:.1f} km"

    def test_symmetry(self):
        lat1, lon1 = COMMUNE_CENTROIDS["NOUMEA"]
        lat2, lon2 = COMMUNE_CENTROIDS["LIFOU"]
        assert abs(haversine_km(lat1, lon1, lat2, lon2) - haversine_km(lat2, lon2, lat1, lon1)) < 1e-6


class TestCommunesWithinRadius:
    def test_noumea_zero_radius(self):
        lat, lon = COMMUNE_CENTROIDS["NOUMEA"]
        # Rayon 0 km : seule Nouméa (centroide exact)
        result = communes_within_radius(lat, lon, 0)
        assert "NOUMEA" in result

    def test_noumea_50km(self):
        lat, lon = COMMUNE_CENTROIDS["NOUMEA"]
        result = communes_within_radius(lat, lon, 50)
        # Communes proches attendues
        for c in ("NOUMEA", "DUMBEA", "PAITA", "MONT-DORE"):
            assert c in result, f"{c} devrait être dans le rayon 50 km de Nouméa"
        # Communes lointaines exclues
        assert "LIFOU" not in result
        assert "BELEP" not in result

    def test_all_nc_500km(self):
        lat, lon = COMMUNE_CENTROIDS["NOUMEA"]
        result = communes_within_radius(lat, lon, 500)
        # Toutes les 33 communes dans un rayon de 500 km depuis Nouméa
        assert len(result) == len(COMMUNE_CENTROIDS)

    def test_empty_ocean_point(self):
        # Point en plein océan loin de la NC
        result = communes_within_radius(-30.0, 170.0, 10)
        assert result == []

    def test_returns_list(self):
        result = communes_within_radius(-22.27, 166.45, 50)
        assert isinstance(result, list)

    def test_all_centroids_present(self):
        assert len(COMMUNE_CENTROIDS) == 33, "33 communes officielles attendues"
