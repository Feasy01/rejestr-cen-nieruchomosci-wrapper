"""Type conversion, CRS transformation, and local filtering."""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from pyproj import Transformer

from app.models import GeoJSONPoint, TransactionItem
from app.services.parser_gml import ParsedFeature

logger = logging.getLogger(__name__)

# Transformers (thread-safe, reusable)
# EPSG:2180 native axis order: northing (Y), easting (X)
# EPSG:4326 native axis order: latitude, longitude
# always_xy=False means we use the CRS native axis order
_to_4326 = Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy=False)
_to_2180 = Transformer.from_crs("EPSG:4326", "EPSG:2180", always_xy=False)


def bbox_4326_to_2180(
    min_lon: float, min_lat: float, max_lon: float, max_lat: float
) -> tuple[float, float, float, float]:
    """Convert BBOX from EPSG:4326 (lon,lat) to EPSG:2180 (northing, easting).

    Input: user-friendly (minLon, minLat, maxLon, maxLat).
    Output: (minNorthing, minEasting, maxNorthing, maxEasting) for upstream BBOX.
    """
    # _to_2180 expects (lat, lon) -> (northing, easting)
    n1, e1 = _to_2180.transform(min_lat, min_lon)
    n2, e2 = _to_2180.transform(max_lat, max_lon)
    return (min(n1, n2), min(e1, e2), max(n1, n2), max(e1, e2))


def _pos_2180_to_4326(
    northing: float, easting: float
) -> tuple[float, float]:
    """Convert a single point from EPSG:2180 to EPSG:4326.

    Returns (latitude, longitude).
    """
    lat, lon = _to_4326.transform(northing, easting)
    return lat, lon


def _safe_decimal(value: str) -> Decimal | None:
    if not value:
        return None
    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def _safe_int(value: str) -> int | None:
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _parse_doc_date(value: str) -> str | None:
    """Extract YYYY-MM-DD from dok_data like '2024-10-02 00:00:00+02'."""
    if not value or len(value) < 10:
        return None
    return value[:10]


def _empty_to_none(value: str) -> str | None:
    return value if value else None


def feature_to_transaction(
    feature: ParsedFeature,
    *,
    include_geometry: bool = False,
    include_raw: bool = False,
    fetched_at: datetime,
) -> TransactionItem:
    """Convert a parsed GML feature to a TransactionItem."""
    p = feature.properties

    geometry: GeoJSONPoint | None = None
    if include_geometry and feature.geometry_pos is not None:
        northing, easting = feature.geometry_pos
        lat, lon = _pos_2180_to_4326(northing, easting)
        geometry = GeoJSONPoint(coordinates=[lon, lat])

    raw: dict[str, Any] | None = None
    if include_raw:
        raw = dict(p)

    return TransactionItem(
        id=feature.gml_id,
        doc_date=_parse_doc_date(p.get("dok_data", "")),
        doc_ref=_empty_to_none(p.get("dok_oznaczenie", "")),
        notary=_empty_to_none(p.get("dok_tworca", "")),
        market=_empty_to_none(p.get("tran_rodzaj_rynku", "")),
        price_brutto=_safe_decimal(p.get("tran_cena_brutto", "")),
        area_uzyt=_safe_decimal(p.get("lok_pow_uzyt", "")),
        function=_empty_to_none(p.get("lok_funkcja", "")),
        rooms=_safe_int(p.get("lok_liczba_izb", "")),
        floor=_empty_to_none(p.get("lok_nr_kond", "")),
        share=_empty_to_none(p.get("nier_udzial", "")),
        geometry=geometry,
        raw=raw,
        fetched_at=fetched_at,
    )


def apply_local_filters(
    features: list[ParsedFeature],
    *,
    date_from: date | None = None,
    date_to: date | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    min_area: Decimal | None = None,
    max_area: Decimal | None = None,
) -> list[ParsedFeature]:
    """Filter features locally on numeric/date fields that can't be
    reliably filtered upstream (because they're stored as strings)."""
    if not any([date_from, date_to, min_price, max_price, min_area, max_area]):
        return features

    result: list[ParsedFeature] = []
    for f in features:
        p = f.properties

        # Date filter
        doc_date = _parse_doc_date(p.get("dok_data", ""))
        if date_from and (not doc_date or doc_date < date_from.isoformat()):
            continue
        if date_to and (not doc_date or doc_date > date_to.isoformat()):
            continue

        # Price filter
        price = _safe_decimal(p.get("tran_cena_brutto", ""))
        if min_price is not None and (price is None or price < min_price):
            continue
        if max_price is not None and (price is None or price > max_price):
            continue

        # Area filter
        area = _safe_decimal(p.get("lok_pow_uzyt", ""))
        if min_area is not None and (area is None or area < min_area):
            continue
        if max_area is not None and (area is None or area > max_area):
            continue

        result.append(f)

    return result
