from __future__ import annotations

import hashlib
import re
import time
from datetime import UTC, date, datetime, timedelta

import requests
from bs4 import BeautifulSoup

from .models import COMMUNES_OFFICIELLES, COMMUNES_PAR_PROVINCE, Maintenance, Province

SOURCE_URL = "https://helia.nc/etat-du-reseau"
NC_TZ = "+11:00"

ALL_COMMUNES = sorted(COMMUNES_OFFICIELLES)

ZONE_TO_COMMUNE: dict[str, str] = {
    "Houailou": "HOUAILOU",
    "Poindimié": "POINDIMIE",
    "Ponerihouen": "PONERIHOUEN",
    "Ponérihouen": "PONERIHOUEN",
    "Hienghene": "HIENGHENE",
    "Mont Dore": "MONT-DORE",
    "Mont-Dore": "MONT-DORE",
    "Koumac": "KOUMAC",
    "Koumax": "KOUMAC",
    "Voh": "VOH",
    "Pouembout": "POUEMBOUT",
    "Boulouparis": "BOULOUPARIS",
    "Koné": "KONE",
    "Bourail": "BOURAIL",
    "Paita": "PAITA",
    "Païta": "PAITA",
    "Farino": "FARINO",
    "Dumbéa": "DUMBEA",
    "Lifou": "LIFOU",
    "Ouvéa": "OUVEA",
    "Kaala Gomen": "KAALA-GOMEN",
    "Kaala-Gomen": "KAALA-GOMEN",
    "La Foa": "LA FOA",
    "Poya": "POYA",
    "Chepenehe": "LIFOU",
    "Gossanah": "LIFOU",
    "Pinhyp": "LIFOU",
    "We": "LIFOU",
    "Wé": "LIFOU",
    "Jozip": "LIFOU",
    "Luengoni": "LIFOU",
    "Hapétra": "LIFOU",
    "Fayahoué": "OUVEA",
    "TADINE (Maré)": "MARE",
    "La Coulée": "MONT-DORE",
    "Plum": "MONT-DORE",
    "Cosmogolf": "MONT-DORE",
    "Koghis": "MONT-DORE",
    "Kafeate": "MONT-DORE",
    "Nouméa": "NOUMEA",
    "Nouméa (Val Plaisance, Anse-Vata)": "NOUMEA",
    "Boulari": "NOUMEA",
    "Robinson": "NOUMEA",
    "Cassis": "NOUMEA",
    "Le Cap": "NOUMEA",
    "Kaméré": "NOUMEA",
    "PK4": "NOUMEA",
    "Tina": "NOUMEA",
    "Tamoa": "PAITA",
    "Tontouta": "PAITA",
    "Katiramona": "PAITA",
    "Beauvallon": "PAITA",
    "Naia": "PAITA",
    "Naïa": "PAITA",
    "Val Suzon": "PAITA",
    "Mont Mou": "PAITA",
    "Tiaré": "PAITA",
    "fayard": "PAITA",
    "Pont des français": "MONT-DORE",
    "Pont des Français": "MONT-DORE",
    "mou": "PAITA",
    "Savannah": "DUMBEA",
    "Zico": "DUMBEA",
    "Koutio": "DUMBEA",
    "Apogoti": "DUMBEA",
    "Apogotti": "DUMBEA",
    "Néméara": "BOURAIL",
    "Paya": "BOURAIL",
    "Nessadiou": "BOURAIL",
    "Boghen": "BOURAIL",
    "Gouaro": "BOURAIL",
    "Ouenghi": "BOULOUPARIS",
    "Bouraké": "BOULOUPARIS",
    "Tomo": "BOULOUPARIS",
    "Nakutakouin": "BOULOUPARIS",
    "Nondoué": "BOULOUPARIS",
    "Ouatom": "BOULOUPARIS",
    "Ouitchambo": "HOUAILOU",
    "Poro": "HOUAILOU",
    "Monea": "HOUAILOU",
    "Vavouto": "KONE",
    "Colnette": "KOUMAC",
    "Ouaco": "KOUMAC",
    "Gomen": "KAALA-GOMEN",
    "Arama": "POUM",
    "Tchamba": "PONERIHOUEN",
    "Coula": "PONERIHOUEN",
    "Kédeigne": "PONERIHOUEN",
    "Kumo": "HIENGHENE",
    "Karikaté": "VOH",
    "Temala": "VOH",
    "Népoui": "POYA",
    "Nepoui": "POYA",
    "Nékou": "POYA",
    "Couli": "MOINDOU",
    "Touho": "TOUHO",
    "Yaté": "YATE",
}

MONTHS = {
    "janvier": 1,
    "février": 2,
    "mars": 3,
    "avril": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7,
    "août": 8,
    "septembre": 9,
    "octobre": 10,
    "novembre": 11,
    "décembre": 12,
}

IMPACT_PATTERNS = [
    (re.compile(r"coupure de 20 à 30", re.I), "COUPURE_20_30_MIN"),
    (re.compile(r"coupure de 30", re.I), "COUPURE_30_MIN"),
]

IMPACT_DUREE: dict[str, tuple[int, int] | None] = {
    "COUPURE_20_30_MIN": (20, 30),
    "COUPURE_30_MIN": (30, 30),
    "A_DETERMINER": None,
}


# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------


def fetch_html(url: str = SOURCE_URL, retries: int = 3, backoff: float = 2.0) -> str:
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            return r.text
        except requests.RequestException as exc:
            if attempt == retries:
                raise RuntimeError(f"Scrape échoué après {retries} tentatives : {exc}") from exc
            time.sleep(backoff**attempt)


# ---------------------------------------------------------------------------
# Parse HTML
# ---------------------------------------------------------------------------


def parse_items(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for block in soup.find_all("div", class_="collapse-item"):
        date_raw = block.find("p", class_="title-accordion").get_text(strip=True)
        for ul in block.find("div", class_="collapse-body").find_all("ul"):
            fields: dict[str, str] = {}
            for li in ul.find_all("li", recursive=False):
                label_tag = li.find("strong")
                if not label_tag:
                    continue
                key = label_tag.get_text(strip=True).rstrip(":").strip()
                val = li.get_text(" ", strip=True)
                val = val.replace(label_tag.get_text(" ", strip=True), "").lstrip(": ").strip()
                fields[key] = val
            if fields:
                items.append({"date": date_raw, **fields})
    return items


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def _parse_date_range(date_str: str) -> tuple[date, date]:
    range_m = re.match(r"^(\d+)\s+au\s+(\d+)\s+(\S+)\s+(\d+)$", date_str)
    list_m = re.match(r"^(\d+(?:-\d+)+)\s+(\S+)\s+(\d+)$", date_str)
    single_m = re.match(r"^(\d+)\s+(\S+)\s+(\d+)$", date_str)
    if range_m:
        d1, d2, month_name, year = range_m.groups()
        m = MONTHS[month_name]
        return date(int(year), m, int(d1)), date(int(year), m, int(d2))
    if list_m:
        days_str, month_name, year = list_m.groups()
        days = [int(d) for d in days_str.split("-")]
        m = MONTHS[month_name]
        return date(int(year), m, min(days)), date(int(year), m, max(days))
    if single_m:
        d, month_name, year = single_m.groups()
        m = MONTHS[month_name]
        s = date(int(year), m, int(d))
        return s, s
    raise ValueError(f"Date non parseable : {date_str!r}")


def _parse_time(s: str) -> tuple[int, int]:
    s = s.lower().replace("h", ":")
    h, _, m = s.partition(":")
    return int(h), int(m or 0)


def _split_zones(zones_str: str) -> list[str]:
    depth, chars, i = 0, [], 0
    while i < len(zones_str):
        c = zones_str[i]
        if c == "(":
            depth += 1
            chars.append(c)
        elif c == ")":
            depth -= 1
            chars.append(c)
        elif depth == 0 and zones_str[i : i + 4] == " et ":
            chars.append(",")
            i += 3
        else:
            chars.append(c)
        i += 1
    parts = re.split(r",\s*(?![^(]*\))", "".join(chars))
    return [p.strip().replace("\xa0", " ") for p in parts if p.strip()]


def _parse_zone_field(zone_str: str) -> list[str]:
    if re.search(r"Impact\s+\w+\s*:", zone_str):
        zone_str = re.sub(r"Impact\s+\w+\s*:\s*", ",", zone_str)
    return _split_zones(zone_str)


def _zones_to_communes(zones: list[str]) -> tuple[list[str], list[str]]:
    if "Nouvelle-Calédonie" in zones:
        return ALL_COMMUNES[:], []
    communes: list[str] = []
    unknown: list[str] = []
    for z in zones:
        commune = ZONE_TO_COMMUNE.get(z)
        if commune is None:
            # Retente sans le suffixe parenthésé : "Koutio (Rue Becquerel)" -> "Koutio"
            base = re.sub(r"\s*\(.*\)\s*$", "", z).strip()
            if base != z:
                commune = ZONE_TO_COMMUNE.get(base)
        if commune is None:
            unknown.append(z)
        elif commune not in communes:
            communes.append(commune)
    return communes, unknown


def _extract_services(text: str) -> list[str]:
    t = text.lower()
    if "céléris" in t or "celeris" in t:
        return ["LIAISONS_CELERIS_ETHERNET"]
    found = []
    if "fixe" in t:
        found.append("TELEPHONIE_FIXE")
        if "internet fixe" in t:
            found.append("INTERNET_FIXE")
    if "mobile" in t:
        found.append("TELEPHONIE_MOBILE")
        if re.search(r"internet\s*(mobile|\xa0mobile)", t):
            found.append("INTERNET_MOBILE")
    if "cuivre" in t:
        found.append("RESEAU_CUIVRE")
    if "fibre" in t:
        found.append("FIBRE_OPTIQUE")
    return found


def _extract_impact(text: str | None) -> str:
    if not text:
        return "A_DETERMINER"
    for pattern, value in IMPACT_PATTERNS:
        if pattern.search(text):
            return value
    return "A_DETERMINER"


def _parse_impacts(impacts_str: str) -> tuple[list[str], str]:
    m = re.match(r"(Coupure de [^s]+?)\s+sur\s+(.+)", impacts_str, re.I)
    if m:
        return _extract_services(m.group(2)), _extract_impact(m.group(1))
    if " - " in impacts_str:
        parts = impacts_str.split(" - ", 1)
        return _extract_services(parts[0]), _extract_impact(parts[1])
    return _extract_services(impacts_str), "A_DETERMINER"


def _to_iso(d: date, h: int, m: int) -> str:
    return f"{d.isoformat()}T{h:02d}:{m:02d}:00{NC_TZ}"


# ---------------------------------------------------------------------------
# Transform
# ---------------------------------------------------------------------------


def _transform(item: dict, scraped_at: str) -> Maintenance:
    date_str = item["date"]
    creneau = item.get("Créneau d'intervention", "")
    zone_raw = item.get("Zone concernée", item.get("Zone concernée :", ""))
    impacts_raw = item.get("Impacts", "")

    debut_raw, fin_raw = creneau.partition(" à ")[::2]
    start, end = _parse_date_range(date_str)
    h_d, m_d = _parse_time(debut_raw.strip())
    h_f, m_f = _parse_time(fin_raw.strip())

    fin_date = end
    if start == end and (h_f, m_f) < (h_d, m_d):
        fin_date = end + timedelta(days=1)

    ts_debut = _to_iso(start, h_d, m_d)
    ts_fin = _to_iso(fin_date, h_f, m_f)

    communes, unknown_zones = _zones_to_communes(_parse_zone_field(zone_raw))
    if not communes:
        raise ValueError(f"Aucune commune reconnue — zones brutes : {_parse_zone_field(zone_raw)}")
    services, impact = _parse_impacts(impacts_raw)

    duree_fenetre = int(
        (datetime.fromisoformat(ts_fin) - datetime.fromisoformat(ts_debut)).total_seconds() // 60
    )
    coupure = IMPACT_DUREE.get(impact)
    fingerprint = "|".join([ts_debut, ts_fin, *sorted(services), *sorted(communes)])

    provinces: list[Province] = []
    for c in communes:
        p = COMMUNES_PAR_PROVINCE.get(c)
        if p and p not in provinces:
            provinces.append(p)

    return Maintenance(
        id=hashlib.sha256(fingerprint.encode()).hexdigest()[:8],
        scraped_at=scraped_at,
        source_url=SOURCE_URL,
        timestamp_debut=ts_debut,
        timestamp_fin=ts_fin,
        duree_fenetre_minutes=duree_fenetre,
        duree_coupure_min_minutes=coupure[0] if coupure else None,
        duree_coupure_max_minutes=coupure[1] if coupure else None,
        communes_concernees=communes,
        services=services,
        impact=impact,
        nb_communes_concernees=len(communes),
        est_toute_nc=len(communes) == len(COMMUNES_OFFICIELLES),
        zones_non_reconnues=unknown_zones or None,
        provinces_concernees=provinces,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def scrape_maintenances(url: str = SOURCE_URL) -> list[Maintenance]:
    import logging

    log = logging.getLogger(__name__)
    scraped_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    html = fetch_html(url)
    items = parse_items(html)
    results: list[Maintenance] = []
    for item in items:
        try:
            results.append(_transform(item, scraped_at))
        except Exception as exc:
            log.warning(
                "Item ignoré (parsing échoué) — %s: %s | item=%r", type(exc).__name__, exc, item
            )
    return results
