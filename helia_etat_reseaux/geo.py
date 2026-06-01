"""Centroides des communes NC et calcul de distance haversine."""
from __future__ import annotations

import math

# Centroides officiels — source : data.gouv.nc
# dataset: communes-nc-limites-terrestres-simplifiees, champ geo_point_2d
COMMUNE_CENTROIDS: dict[str, tuple[float, float]] = {
    "NOUMEA":       (-22.257800, 166.450090),
    "DUMBEA":       (-22.126546, 166.493736),
    "PAITA":        (-22.040971, 166.316636),
    "MONT-DORE":    (-22.275665, 166.728493),
    "BOULOUPARIS":  (-21.859259, 166.111898),
    "YATE":         (-22.083508, 166.724866),
    "ILE DES PINS": (-22.612532, 167.479871),
    "LA FOA":       (-21.722727, 165.880453),
    "FARINO":       (-21.648246, 165.759219),
    "SARRAMEA":     (-21.622340, 165.818967),
    "MOINDOU":      (-21.625926, 165.674933),
    "BOURAIL":      (-21.534368, 165.461729),
    "THIO":         (-21.724381, 166.256520),
    "CANALA":       (-21.531276, 165.968968),
    "KOUAOUA":      (-21.458301, 165.782577),
    "HOUAILOU":     (-21.330198, 165.549981),
    "PONERIHOUEN":  (-21.131155, 165.315489),
    "POINDIMIE":    (-20.948387, 165.175839),
    "TOUHO":        (-20.817968, 165.157733),
    "POYA":         (-21.330607, 165.210350),
    "POUEMBOUT":    (-21.167138, 165.000992),
    "KONE":         (-21.026262, 164.906408),
    "VOH":          (-20.868914, 164.734178),
    "KAALA-GOMEN":  (-20.700238, 164.513140),
    "KOUMAC":       (-20.503308, 164.328171),
    "POUM":         (-20.262885, 164.147684),
    "OUEGOA":       (-20.408064, 164.465065),
    "POUEBO":       (-20.414186, 164.597588),
    "BELEP":        (-19.693145, 163.650235),
    "HIENGHENE":    (-20.716141, 164.845422),
    "LIFOU":        (-20.944989, 167.238656),
    "MARE":         (-21.514954, 167.970418),
    "OUVEA":        (-20.563597, 166.562699),
}

_R_EARTH_KM = 6371.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance en km entre deux points (degrés décimaux)."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return _R_EARTH_KM * 2 * math.asin(math.sqrt(a))


def communes_within_radius(lat: float, lon: float, radius_km: float) -> list[str]:
    """Retourne les noms de communes dont le centroide est dans le rayon donné."""
    return [
        nom
        for nom, (clat, clon) in COMMUNE_CENTROIDS.items()
        if haversine_km(lat, lon, clat, clon) <= radius_km
    ]
