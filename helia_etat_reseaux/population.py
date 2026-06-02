"""Population municipale des communes NC — recensement ISEE 2019.

Source : data.gouv.nc, dataset `population-legale-de-la-nouvelle-caledonie`,
champ `population_municipale` (1).
Jointure via `commune_maj` (clé en majuscules, identique à COMMUNES_OFFICIELLES).
"""

from __future__ import annotations

# Population municipale (1) — recensement 2019
# https://data.gouv.nc/explore/dataset/population-legale-de-la-nouvelle-caledonie
COMMUNE_POPULATION: dict[str, int] = {
    "BELEP": 867,
    "BOULOUPARIS": 3315,
    "BOURAIL": 5531,
    "CANALA": 3701,
    "DUMBEA": 35873,
    "FARINO": 712,
    "HIENGHENE": 2454,
    "HOUAILOU": 3955,
    "ILE DES PINS": 2037,
    "KAALA-GOMEN": 1803,
    "KONE": 8144,
    "KOUAOUA": 1304,
    "KOUMAC": 3981,
    "LA FOA": 3552,
    "LIFOU": 9195,
    "MARE": 5757,
    "MOINDOU": 681,
    "MONT-DORE": 27620,
    "NOUMEA": 94285,
    "OUEGOA": 2118,
    "OUVEA": 3401,
    "PAITA": 24563,
    "POINDIMIE": 5006,
    "PONERIHOUEN": 2420,
    "POUEBO": 2144,
    "POUEMBOUT": 2752,
    "POUM": 1435,
    "POYA": 2802,
    "SARRAMEA": 572,
    "THIO": 2524,
    "TOUHO": 2380,
    "VOH": 2856,
    "YATE": 1667,
}

RECENSEMENT_ANNEE = 2019
