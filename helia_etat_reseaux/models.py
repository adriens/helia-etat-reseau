from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, Field, computed_field, field_validator, model_validator
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema


class Province(StrEnum):
    """Province administrative de Nouvelle-Calédonie."""

    PROVINCE_SUD = "PROVINCE_SUD"
    PROVINCE_NORD = "PROVINCE_NORD"
    ILES_LOYAUTE = "ILES_LOYAUTE"

    @classmethod
    def __get_pydantic_json_schema__(cls, schema: CoreSchema, handler: Any) -> JsonSchemaValue:
        js = handler(schema)
        js["description"] = "Province administrative NC."
        js["x-enumDescriptions"] = {
            "PROVINCE_SUD": "Province Sud (Nouméa, Grand Nouméa, intérieur sud)",
            "PROVINCE_NORD": "Province Nord (côte ouest et est, extrême nord)",
            "ILES_LOYAUTE": "Province des Îles Loyauté (Lifou, Maré, Ouvéa)",
        }
        return js


COMMUNES_PAR_PROVINCE: dict[str, Province] = {
    # Province Sud
    "BOULOUPARIS": Province.PROVINCE_SUD,
    "BOURAIL": Province.PROVINCE_SUD,
    "DUMBEA": Province.PROVINCE_SUD,
    "FARINO": Province.PROVINCE_SUD,
    "ILE DES PINS": Province.PROVINCE_SUD,
    "LA FOA": Province.PROVINCE_SUD,
    "MOINDOU": Province.PROVINCE_SUD,
    "MONT-DORE": Province.PROVINCE_SUD,
    "NOUMEA": Province.PROVINCE_SUD,
    "PAITA": Province.PROVINCE_SUD,
    "SARRAMEA": Province.PROVINCE_SUD,
    "THIO": Province.PROVINCE_SUD,
    "YATE": Province.PROVINCE_SUD,
    # Province Nord
    "BELEP": Province.PROVINCE_NORD,
    "CANALA": Province.PROVINCE_NORD,
    "HIENGHENE": Province.PROVINCE_NORD,
    "HOUAILOU": Province.PROVINCE_NORD,
    "KAALA-GOMEN": Province.PROVINCE_NORD,
    "KONE": Province.PROVINCE_NORD,
    "KOUAOUA": Province.PROVINCE_NORD,
    "KOUMAC": Province.PROVINCE_NORD,
    "OUEGOA": Province.PROVINCE_NORD,
    "POINDIMIE": Province.PROVINCE_NORD,
    "PONERIHOUEN": Province.PROVINCE_NORD,
    "POUEBO": Province.PROVINCE_NORD,
    "POUEMBOUT": Province.PROVINCE_NORD,
    "POUM": Province.PROVINCE_NORD,
    "POYA": Province.PROVINCE_NORD,
    "TOUHO": Province.PROVINCE_NORD,
    "VOH": Province.PROVINCE_NORD,
    # Îles Loyauté
    "LIFOU": Province.ILES_LOYAUTE,
    "MARE": Province.ILES_LOYAUTE,
    "OUVEA": Province.ILES_LOYAUTE,
}


class Service(StrEnum):
    """Services télécoms pouvant être impactés lors d'une maintenance."""

    TELEPHONIE_FIXE = "TELEPHONIE_FIXE"
    TELEPHONIE_MOBILE = "TELEPHONIE_MOBILE"
    INTERNET_FIXE = "INTERNET_FIXE"
    INTERNET_MOBILE = "INTERNET_MOBILE"
    FIBRE_OPTIQUE = "FIBRE_OPTIQUE"
    RESEAU_CUIVRE = "RESEAU_CUIVRE"
    LIAISONS_CELERIS_ETHERNET = "LIAISONS_CELERIS_ETHERNET"

    @classmethod
    def __get_pydantic_json_schema__(cls, schema: CoreSchema, handler: Any) -> JsonSchemaValue:
        js = handler(schema)
        js["description"] = "Service télécom impacté par la maintenance."
        js["x-enumDescriptions"] = {
            "TELEPHONIE_FIXE": "Téléphonie fixe (RTC / VoIP fixe)",
            "TELEPHONIE_MOBILE": "Téléphonie mobile (voix)",
            "INTERNET_FIXE": "Accès Internet fixe (ADSL, fibre, cuivre)",
            "INTERNET_MOBILE": "Accès Internet mobile (4G/5G)",
            "FIBRE_OPTIQUE": "Réseau fibre optique",
            "RESEAU_CUIVRE": "Réseau cuivre (paires téléphoniques)",
            "LIAISONS_CELERIS_ETHERNET": "Liaisons Ethernet dédiées Céléris (offres entreprises)",
        }
        return js


class GeoPoint(BaseModel):
    """Coordonnées géographiques — compatible champ `geo_point` OpenSearch."""

    lat: float = Field(description="Latitude en degrés décimaux (WGS 84).")
    lon: float = Field(description="Longitude en degrés décimaux (WGS 84).")


class CommuneGeoPoint(BaseModel):
    """Centroïde d'une commune NC — compatible champ `nested` + `geo_point` OpenSearch."""

    commune: str = Field(description="Nom officiel de la commune.")
    lat: float = Field(description="Latitude du centroïde (WGS 84).")
    lon: float = Field(description="Longitude du centroïde (WGS 84).")


class Impact(StrEnum):
    """Sévérité estimée de la coupure effective pour les utilisateurs."""

    COUPURE_20_30_MIN = "COUPURE_20_30_MIN"
    COUPURE_30_MIN = "COUPURE_30_MIN"
    A_DETERMINER = "A_DETERMINER"

    @classmethod
    def __get_pydantic_json_schema__(cls, schema: CoreSchema, handler: Any) -> JsonSchemaValue:
        js = handler(schema)
        js["description"] = "Sévérité de l'impact sur les utilisateurs finals."
        js["x-enumDescriptions"] = {
            "COUPURE_20_30_MIN": "Coupure effective estimée entre 20 et 30 minutes",
            "COUPURE_30_MIN": "Coupure effective estimée à 30 minutes",
            "A_DETERMINER": "Durée d'impact non encore déterminée",
        }
        return js


COMMUNES_OFFICIELLES = frozenset(
    [
        "BELEP",
        "BOULOUPARIS",
        "BOURAIL",
        "CANALA",
        "DUMBEA",
        "FARINO",
        "HIENGHENE",
        "HOUAILOU",
        "ILE DES PINS",
        "KAALA-GOMEN",
        "KONE",
        "KOUAOUA",
        "KOUMAC",
        "LA FOA",
        "LIFOU",
        "MARE",
        "MOINDOU",
        "MONT-DORE",
        "NOUMEA",
        "OUEGOA",
        "OUVEA",
        "PAITA",
        "POINDIMIE",
        "PONERIHOUEN",
        "POUEBO",
        "POUEMBOUT",
        "POUM",
        "POYA",
        "SARRAMEA",
        "THIO",
        "TOUHO",
        "VOH",
        "YATE",
    ]
)


class Maintenance(BaseModel):
    """
    Maintenance programmée sur le réseau télécoms Helia (OPT-NC).

    Chaque objet représente une fenêtre de maintenance planifiée, avec les
    communes concernées, les services impactés et l'estimation de coupure.
    """

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "a6cec665",
                "scraped_at": "2026-06-01T10:00:00Z",
                "source_url": "https://helia.nc/etat-du-reseau",
                "timestamp_debut": "2026-06-01T23:00:00+11:00",
                "timestamp_fin": "2026-06-02T05:00:00+11:00",
                "duree_fenetre_minutes": 360,
                "duree_coupure_min_minutes": 20,
                "duree_coupure_max_minutes": 30,
                "communes_concernees": ["HOUAILOU", "POINDIMIE", "KONE"],
                "services": ["TELEPHONIE_FIXE", "INTERNET_FIXE"],
                "impact": "COUPURE_20_30_MIN",
            }
        }
    }

    id: Annotated[
        str,
        Field(
            pattern=r"^[0-9a-f]{8}$",
            description=(
                "Identifiant SHA256 tronqué à 8 caractères hexadécimaux, "
                "calculé à partir de `timestamp_debut`, `timestamp_fin`, `services` (triés) "
                "et `communes_concernees` (triées). "
                "**Stable entre deux scrapes** si la maintenance n'a pas changé : "
                "permet l'idempotence dans Kafka et l'upsert dans OpenSearch (`_id`)."
            ),
        ),
    ]
    scraped_at: Annotated[
        str,
        Field(
            description="Horodatage UTC du scrape, au format `YYYY-MM-DDTHH:MM:SSZ`.",
        ),
    ]
    source_url: Annotated[
        str,
        Field(
            description="URL de la page source scrapée.",
        ),
    ]
    timestamp_debut: Annotated[
        str,
        Field(
            description=(
                "Début de la fenêtre de maintenance au format ISO 8601, "
                "heure locale Nouvelle-Calédonie **UTC+11** (pas de changement d'heure). "
                "Exemple : `2026-06-01T23:00:00+11:00`."
            ),
        ),
    ]
    timestamp_fin: Annotated[
        str,
        Field(
            description=(
                "Fin de la fenêtre de maintenance au format ISO 8601, "
                "heure locale Nouvelle-Calédonie **UTC+11**. "
                "Peut tomber le lendemain pour les fenêtres nocturnes (ex: 23h→5h)."
            ),
        ),
    ]
    duree_fenetre_minutes: Annotated[
        int,
        Field(
            gt=0,
            description=(
                "Durée totale de la fenêtre de maintenance en minutes, "
                "calculée comme `timestamp_fin − timestamp_debut`. "
                "Distinct de la durée de coupure effective."
            ),
        ),
    ]
    duree_coupure_min_minutes: Annotated[
        int | None,
        Field(
            description=(
                "Durée **minimale** estimée de la coupure effective en minutes. "
                "`null` si `impact` vaut `A_DETERMINER`."
            ),
        ),
    ]
    duree_coupure_max_minutes: Annotated[
        int | None,
        Field(
            description=(
                "Durée **maximale** estimée de la coupure effective en minutes. "
                "`null` si `impact` vaut `A_DETERMINER`."
            ),
        ),
    ]
    communes_concernees: Annotated[
        list[str],
        Field(
            min_length=1,
            description=(
                "Liste des communes officielles NC affectées, en majuscules. "
                "Normalisées selon le référentiel "
                "[communes-nc-limites-terrestres-simplifiees](https://data.gouv.nc/explore/dataset/communes-nc-limites-terrestres-simplifiees/) "
                "de data.gouv.nc — jointure directe possible sur le champ `nom`."
            ),
        ),
    ]
    services: Annotated[
        list[Service],
        Field(
            min_length=1,
            description="Liste des services télécoms impactés par cette maintenance.",
        ),
    ]
    impact: Annotated[
        Impact,
        Field(
            description="Sévérité estimée de la coupure effective pour les abonnés.",
        ),
    ]
    nb_communes_concernees: Annotated[
        int,
        Field(
            gt=0,
            description="Nombre de communes officielles affectées. Pratique pour agréger l'étendue géographique.",
        ),
    ]
    est_toute_nc: Annotated[
        bool,
        Field(
            description="`true` si les 33 communes de Nouvelle-Calédonie sont toutes concernées.",
        ),
    ]
    provinces_concernees: Annotated[
        list[Province],
        Field(
            min_length=1,
            description=(
                "Provinces administratives NC concernées, dérivées de `communes_concernees`. "
                "Utile pour filtrer par grande zone géographique."
            ),
        ),
    ]

    @field_validator("communes_concernees")
    @classmethod
    def communes_must_be_official(cls, v: list[str]) -> list[str]:
        unknown = [c for c in v if c not in COMMUNES_OFFICIELLES]
        if unknown:
            raise ValueError(f"Communes non officielles : {unknown}")
        return v

    @model_validator(mode="after")
    def duree_coupure_coherence(self) -> Maintenance:
        mn, mx = self.duree_coupure_min_minutes, self.duree_coupure_max_minutes
        if (mn is None) != (mx is None):
            raise ValueError(
                "duree_coupure_min et max doivent être tous les deux None ou renseignés"
            )
        if mn is not None and mx is not None and mn > mx:
            raise ValueError(f"duree_coupure_min ({mn}) > duree_coupure_max ({mx})")
        if self.impact == Impact.A_DETERMINER and mn is not None:
            raise ValueError("impact A_DETERMINER mais duree_coupure renseignée")
        if self.impact != Impact.A_DETERMINER and mn is None:
            raise ValueError(f"impact {self.impact} mais duree_coupure est None")
        return self

    @model_validator(mode="after")
    def timestamps_coherence(self) -> Maintenance:
        if self.timestamp_fin <= self.timestamp_debut:
            raise ValueError("timestamp_fin <= timestamp_debut")
        return self

    @computed_field(
        description=(
            "Centroïdes des communes concernées — un point par commune. "
            "Mapper en `nested` + `geo_point` dans OpenSearch."
        )
    )
    @property
    def communes_geopoints(self) -> list[CommuneGeoPoint]:
        from .geo import COMMUNE_CENTROIDS

        return [
            CommuneGeoPoint(commune=c, lat=COMMUNE_CENTROIDS[c][0], lon=COMMUNE_CENTROIDS[c][1])
            for c in self.communes_concernees
            if c in COMMUNE_CENTROIDS
        ]

    @computed_field(
        description=(
            "Centroïde moyen de la maintenance (moyenne des centroïdes des communes impactées). "
            "Mapper en `geo_point` dans OpenSearch pour les requêtes de proximité."
        )
    )
    @property
    def centroide(self) -> GeoPoint:
        from .geo import COMMUNE_CENTROIDS

        pts = [COMMUNE_CENTROIDS[c] for c in self.communes_concernees if c in COMMUNE_CENTROIDS]
        return GeoPoint(
            lat=sum(p[0] for p in pts) / len(pts),
            lon=sum(p[1] for p in pts) / len(pts),
        )
