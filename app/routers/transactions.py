from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Annotated, Any, Literal

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from app.core.cache import features_cache, get_or_fetch, make_cache_key
from app.core.config import settings
from app.models import TransactionItem, TransactionListResponse
from app.services.parser_gml import parse_feature_collection
from app.services.transform import (
    apply_local_filters,
    bbox_4326_to_2180,
    feature_to_transaction,
    sort_items,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/transactions", tags=["transactions"])

SORT_FIELDS = {"price_brutto", "area_uzyt", "price_per_sqm", "doc_date", "rooms"}


@router.get("/lokale", response_model=TransactionListResponse)
async def get_lokale(
    request: Request,
    bbox: Annotated[
        str | None,
        Query(
            description="minLon,minLat,maxLon,maxLat in EPSG:4326",
            pattern=r"^-?\d+\.?\d*,-?\d+\.?\d*,-?\d+\.?\d*,-?\d+\.?\d*$",
        ),
    ] = None,
    date_from: Annotated[date | None, Query(description="YYYY-MM-DD")] = None,
    date_to: Annotated[date | None, Query(description="YYYY-MM-DD")] = None,
    market: Annotated[
        Literal["pierwotny", "wtorny"] | None,
        Query(description="pierwotny or wtorny"),
    ] = None,
    function: Annotated[
        str | None, Query(description="e.g. mieszkalna")
    ] = None,
    min_area: Annotated[
        Decimal | None, Query(description="Min usable area (m²)")
    ] = None,
    max_area: Annotated[
        Decimal | None, Query(description="Max usable area (m²)")
    ] = None,
    min_price: Annotated[
        Decimal | None, Query(description="Min gross price (PLN)")
    ] = None,
    max_price: Annotated[
        Decimal | None, Query(description="Max gross price (PLN)")
    ] = None,
    min_price_per_sqm: Annotated[
        Decimal | None, Query(description="Min price per m² (PLN/m²)")
    ] = None,
    max_price_per_sqm: Annotated[
        Decimal | None, Query(description="Max price per m² (PLN/m²)")
    ] = None,
    sort_by: Annotated[
        str | None,
        Query(description="Sort field: price_brutto, area_uzyt, price_per_sqm, doc_date, rooms"),
    ] = None,
    sort_order: Annotated[
        Literal["asc", "desc"], Query(description="Sort order")
    ] = "asc",
    format: Annotated[
        Literal["json", "geojson"] | None,
        Query(description="Response format: json (default) or geojson"),
    ] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=500)] = 100,
    include_geometry: bool = False,
    include_raw: bool = False,
) -> TransactionListResponse | JSONResponse:
    # Validate sort_by
    if sort_by and sort_by not in SORT_FIELDS:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid sort_by: {sort_by}. Must be one of: {', '.join(sorted(SORT_FIELDS))}",
        )

    # GeoJSON format implies geometry
    geojson_mode = format == "geojson"
    if geojson_mode:
        include_geometry = True

    rcn_client = request.app.state.rcn_client

    # Convert BBOX from user 4326 to upstream 2180
    bbox_2180: tuple[float, float, float, float] | None = None
    if bbox:
        parts = [float(x) for x in bbox.split(",")]
        bbox_2180 = bbox_4326_to_2180(parts[0], parts[1], parts[2], parts[3])

    start_index = (page - 1) * page_size

    # Build cache key from upstream-relevant params only
    cache_params = {
        "bbox_2180": bbox_2180,
        "market": market,
        "function": function,
        "count": page_size,
        "start_index": start_index,
    }
    cache_key = make_cache_key(cache_params)

    # Fetch from upstream (or cache)
    try:
        xml_bytes, cache_hit = await get_or_fetch(
            features_cache,
            cache_key,
            lambda: rcn_client.get_feature(
                bbox_2180=bbox_2180,
                market=market,
                function=function,
                count=page_size,
                start_index=start_index,
            ),
        )
    except Exception:
        logger.exception("Upstream WFS request failed")
        raise HTTPException(
            status_code=502,
            detail="Upstream WFS service unavailable",
        )

    logger.info("Cache %s for key %s", "HIT" if cache_hit else "MISS", cache_key[:12])

    # Parse GML
    parsed = parse_feature_collection(xml_bytes)

    # Apply local filters (date, price, area, price_per_sqm)
    filtered = apply_local_filters(
        parsed.features,
        date_from=date_from,
        date_to=date_to,
        min_price=min_price,
        max_price=max_price,
        min_area=min_area,
        max_area=max_area,
        min_price_per_sqm=min_price_per_sqm,
        max_price_per_sqm=max_price_per_sqm,
    )

    # Transform to API models
    now = datetime.now(timezone.utc)
    items = [
        feature_to_transaction(
            f,
            include_geometry=include_geometry,
            include_raw=include_raw,
            fetched_at=now,
        )
        for f in filtered
    ]

    # Sort items (local, since upstream doesn't support reliable sorting)
    if sort_by:
        items = sort_items(items, sort_by=sort_by, descending=(sort_order == "desc"))

    # Pagination: next_page if upstream returned a full page
    next_page = page + 1 if parsed.number_returned >= page_size else None

    # GeoJSON output
    if geojson_mode:
        return _build_geojson_response(items, page=page, page_size=page_size, next_page=next_page)

    return TransactionListResponse(
        page=page,
        page_size=page_size,
        next_page=next_page,
        items=items,
    )


def _build_geojson_response(
    items: list[TransactionItem],
    *,
    page: int,
    page_size: int,
    next_page: int | None,
) -> JSONResponse:
    """Build a GeoJSON FeatureCollection from TransactionItems."""
    features: list[dict[str, Any]] = []
    for item in items:
        coords = item.geometry.coordinates if item.geometry else [0.0, 0.0]
        properties = {
            "id": item.id,
            "doc_date": item.doc_date,
            "market": item.market,
            "price_brutto": float(item.price_brutto) if item.price_brutto else None,
            "area_uzyt": float(item.area_uzyt) if item.area_uzyt else None,
            "price_per_sqm": float(item.price_per_sqm) if item.price_per_sqm else None,
            "function": item.function,
            "rooms": item.rooms,
            "floor": item.floor,
        }
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": coords},
            "properties": properties,
        })

    collection: dict[str, Any] = {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "page": page,
            "page_size": page_size,
            "next_page": next_page,
            "count": len(features),
        },
    }
    return JSONResponse(content=collection)
