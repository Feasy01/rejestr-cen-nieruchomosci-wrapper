from __future__ import annotations

import asyncio
import logging
from typing import Any
from urllib.parse import quote

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_SRSNAME = "urn:ogc:def:crs:EPSG::2180"

_OGC_FILTER_NS = "http://www.opengis.net/ogc"
_GML_FILTER_NS = "http://www.opengis.net/gml"


def _build_ogc_filter(
    *,
    bbox_2180: tuple[float, float, float, float] | None = None,
    market: str | None = None,
    function: str | None = None,
) -> str | None:
    """Build an OGC XML Filter string for the FILTER KVP parameter.

    bbox_2180: (minY, minX, maxY, maxX) in EPSG:2180 (northing, easting order).
    """
    parts: list[str] = []

    if bbox_2180 is not None:
        min_y, min_x, max_y, max_x = bbox_2180
        parts.append(
            f"<BBOX>"
            f"<PropertyName>msGeometry</PropertyName>"
            f'<gml:Envelope srsName="{_SRSNAME}">'
            f"<gml:lowerCorner>{min_y} {min_x}</gml:lowerCorner>"
            f"<gml:upperCorner>{max_y} {max_x}</gml:upperCorner>"
            f"</gml:Envelope>"
            f"</BBOX>"
        )

    if market:
        parts.append(
            f"<PropertyIsEqualTo>"
            f"<PropertyName>tran_rodzaj_rynku</PropertyName>"
            f"<Literal>{market}</Literal>"
            f"</PropertyIsEqualTo>"
        )

    if function:
        parts.append(
            f"<PropertyIsEqualTo>"
            f"<PropertyName>lok_funkcja</PropertyName>"
            f"<Literal>{function}</Literal>"
            f"</PropertyIsEqualTo>"
        )

    if not parts:
        return None

    inner = "".join(parts)
    if len(parts) > 1:
        inner = f"<And>{inner}</And>"

    return (
        f'<Filter xmlns="{_OGC_FILTER_NS}" xmlns:gml="{_GML_FILTER_NS}">'
        f"{inner}"
        f"</Filter>"
    )


class RCNClient:
    """Async client for the RCN WFS service."""

    def __init__(self, http_client: httpx.AsyncClient) -> None:
        self._client = http_client

    async def _request(self, params: dict[str, str]) -> bytes:
        """Send a GET request with retries and backoff."""
        last_exc: Exception | None = None
        max_attempts = 1 + settings.upstream_max_retries

        for attempt in range(max_attempts):
            try:
                resp = await self._client.get(
                    settings.wfs_base_url, params=params
                )
                resp.raise_for_status()
                return resp.content
            except (httpx.HTTPStatusError, httpx.TransportError) as exc:
                last_exc = exc
                if attempt < max_attempts - 1:
                    delay = settings.upstream_retry_backoff[
                        min(attempt, len(settings.upstream_retry_backoff) - 1)
                    ]
                    logger.warning(
                        "Upstream request failed (attempt %d/%d), retrying in %.1fs: %s",
                        attempt + 1,
                        max_attempts,
                        delay,
                        exc,
                    )
                    await asyncio.sleep(delay)

        raise last_exc  # type: ignore[misc]

    async def get_feature(
        self,
        *,
        bbox_2180: tuple[float, float, float, float] | None = None,
        market: str | None = None,
        function: str | None = None,
        count: int = 100,
        start_index: int = 0,
    ) -> bytes:
        """Fetch features from ms:lokale layer."""
        params: dict[str, str] = {
            "SERVICE": "WFS",
            "REQUEST": "GetFeature",
            "VERSION": "2.0.0",
            "TYPENAMES": "ms:lokale",
            "SRSNAME": _SRSNAME,
            "COUNT": str(count),
            "STARTINDEX": str(start_index),
        }

        ogc_filter = _build_ogc_filter(
            bbox_2180=bbox_2180, market=market, function=function
        )

        if ogc_filter is not None:
            params["FILTER"] = ogc_filter
        elif bbox_2180 is not None:
            min_y, min_x, max_y, max_x = bbox_2180
            params["BBOX"] = f"{min_y},{min_x},{max_y},{max_x},{_SRSNAME}"

        logger.info(
            "WFS GetFeature: count=%d startindex=%d filter=%s",
            count,
            start_index,
            "yes" if ogc_filter else "no",
        )
        return await self._request(params)

    async def get_capabilities(self) -> bytes:
        params = {
            "SERVICE": "WFS",
            "REQUEST": "GetCapabilities",
            "VERSION": "2.0.0",
        }
        return await self._request(params)

    async def describe_feature_type(
        self, typename: str = "ms:lokale"
    ) -> bytes:
        params = {
            "SERVICE": "WFS",
            "REQUEST": "DescribeFeatureType",
            "VERSION": "2.0.0",
            "TYPENAMES": typename,
        }
        return await self._request(params)
