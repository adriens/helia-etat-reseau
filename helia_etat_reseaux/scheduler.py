"""Scheduler APScheduler — scrape périodique et archivage en SQLite.

Intervalle contrôlé par la variable d'environnement HELIA_SCRAPE_INTERVAL_MINUTES
(défaut : 15). Minimum autorisé : 5 minutes.
"""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from helia_etat_reseaux import scrape_maintenances
from helia_etat_reseaux.db import init_db, upsert_run

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None

_DEFAULT_INTERVAL = int(os.environ.get("HELIA_SCRAPE_INTERVAL_MINUTES", "15"))
_MIN_INTERVAL = 5


def _scrape_job() -> None:
    ts = datetime.now(UTC).isoformat()
    try:
        items = [m.model_dump(mode="json") for m in scrape_maintenances()]
        run_id = upsert_run(items, scraped_at=ts)
        logger.info("Scrape OK run_id=%d nb=%d", run_id, len(items))
    except Exception as exc:
        upsert_run([], scraped_at=ts, error=str(exc))
        logger.error("Scrape FAILED: %s", exc)


def start_scheduler(interval_minutes: int | None = None) -> AsyncIOScheduler:
    global _scheduler
    minutes = max(
        _MIN_INTERVAL, interval_minutes if interval_minutes is not None else _DEFAULT_INTERVAL
    )
    init_db()
    # Run immediately on startup
    _scrape_job()

    _scheduler = AsyncIOScheduler(timezone="UTC")
    _scheduler.add_job(
        _scrape_job,
        trigger=IntervalTrigger(minutes=minutes),
        id="helia_scrape",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("Scheduler started — interval=%d min", minutes)
    return _scheduler


def stop_scheduler() -> None:
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
