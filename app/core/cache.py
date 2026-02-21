from __future__ import annotations

import hashlib
import json
from collections.abc import Awaitable, Callable
from typing import Any

from cachetools import TTLCache

from app.core.config import settings

features_cache: TTLCache[str, Any] = TTLCache(
    maxsize=settings.cache_max_size,
    ttl=settings.cache_ttl_features,
)

metadata_cache: TTLCache[str, Any] = TTLCache(
    maxsize=16,
    ttl=settings.cache_ttl_metadata,
)


def make_cache_key(params: dict[str, Any]) -> str:
    raw = json.dumps(params, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


async def get_or_fetch(
    cache: TTLCache[str, Any],
    key: str,
    fetch_fn: Callable[[], Awaitable[Any]],
) -> tuple[Any, bool]:
    """Return (value, cache_hit). Fetches and stores on miss."""
    if key in cache:
        return cache[key], True
    value = await fetch_fn()
    cache[key] = value
    return value, False
