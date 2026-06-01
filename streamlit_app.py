"""Dashboard Streamlit — Helia NC maintenances."""
import json
import os
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from helia_etat_reseaux.db import DB_PATH, get_latest_maintenances, get_scrape_runs, init_db

st.set_page_config(
    page_title="Helia NC — Dashboard",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📡 Helia NC — Maintenances réseau")
st.caption(f"Base SQLite : `{DB_PATH}`")

# ── Init DB if needed ──────────────────────────────────────────────────────────
if not DB_PATH.exists():
    st.warning("Base SQLite introuvable. Initialisation…")
    init_db()

# ── Sidebar filters ────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filtres")
    commune_filter = st.text_input("Commune", placeholder="ex: NOUMEA").upper().strip() or None
    province_filter = st.selectbox(
        "Province",
        ["", "PROVINCE_SUD", "PROVINCE_NORD", "ILES_LOYAUTE"],
        format_func=lambda x: x or "Toutes",
    ) or None
    service_filter = st.selectbox(
        "Service",
        ["", "TELEPHONIE_FIXE", "TELEPHONIE_MOBILE", "INTERNET_FIXE", "INTERNET_MOBILE", "TELEVISION"],
        format_func=lambda x: x.replace("_", " ") if x else "Tous",
    ) or None

    st.divider()
    st.header("Scrapes récents")
    runs = get_scrape_runs(limit=10)
    if runs:
        for r in runs:
            icon = "✅" if r["status"] == "ok" else "❌"
            ts = r["scraped_at"][:19].replace("T", " ")
            st.markdown(f"{icon} `{ts}` — {r['nb_items']} items")
    else:
        st.info("Aucun scrape enregistré.")

# ── Main content ───────────────────────────────────────────────────────────────
maintenances = get_latest_maintenances(
    commune=commune_filter,
    province=province_filter,
    service=service_filter,
)

if not maintenances:
    st.info("Aucune maintenance trouvée avec ces filtres. La base est peut-être vide — attendez le prochain scrape.")
    st.stop()

# KPIs
col1, col2, col3, col4 = st.columns(4)
col1.metric("Maintenances", len(maintenances))
col2.metric("Toute NC", sum(1 for m in maintenances if m["est_toute_nc"]))
all_communes = {c for m in maintenances for c in m["communes_concernees"]}
col3.metric("Communes impactées", len(all_communes))
all_services = {s for m in maintenances for s in m["services"]}
col4.metric("Services impactés", len(all_services))

st.divider()

# Table
rows = []
for m in maintenances:
    rows.append({
        "ID": m["id"],
        "Début": m["timestamp_debut"][:16].replace("T", " "),
        "Fin": m["timestamp_fin"][:16].replace("T", " "),
        "Durée (min)": m["duree_fenetre_minutes"],
        "Communes": ", ".join(m["communes_concernees"]),
        "Services": ", ".join(s.replace("_", " ") for s in m["services"]),
        "Impact": m["impact"].replace("_", " "),
        "Provinces": ", ".join(m["provinces_concernees"]),
        "Toute NC": "✓" if m["est_toute_nc"] else "",
    })

df = pd.DataFrame(rows)

st.subheader(f"Maintenances ({len(df)})")
st.dataframe(df, use_container_width=True, hide_index=True)

st.divider()

# Charts
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Par impact")
    impact_counts = pd.Series([m["impact"] for m in maintenances]).value_counts()
    st.bar_chart(impact_counts)

with col_b:
    st.subheader("Par service")
    service_counts = pd.Series(
        [s for m in maintenances for s in m["services"]]
    ).value_counts()
    st.bar_chart(service_counts)

# Commune coverage
st.subheader("Communes les plus impactées")
commune_counts = pd.Series(
    [c for m in maintenances for c in m["communes_concernees"]]
).value_counts().head(15)
st.bar_chart(commune_counts)
