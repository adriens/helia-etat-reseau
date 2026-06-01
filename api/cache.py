"""Cache TTL en mémoire pour les lookups fréquents.

Utilise cachetools.TTLCache (thread-safe avec Lock).
TTL par défaut : 300s (5 min). Configurable via HELIA_CACHE_TTL_SECONDS.
"""

from __future__ import annotations

import os
import threading
from typing import Any

import cachetools

_TTL = int(os.environ.get("HELIA_CACHE_TTL_SECONDS", "300"))
_MAX = int(os.environ.get("HELIA_CACHE_MAX_SIZE", "256"))

_cache: cachetools.TTLCache = cachetools.TTLCache(maxsize=_MAX, ttl=_TTL)
_lock = threading.Lock()


def get(key: str) -> Any | None:
    with _lock:
        return _cache.get(key)


def set(key: str, value: Any) -> None:
    with _lock:
        _cache[key] = value


def invalidate(key: str) -> None:
    with _lock:
        _cache.pop(key, None)


def clear() -> None:
    with _lock:
        _cache.clear()


def stats() -> dict:
    with _lock:
        return {
            "size": len(_cache),
            "maxsize": _cache.maxsize,
            "ttl_seconds": _TTL,
            "currsize": _cache.currsize,
        }
