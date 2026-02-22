from __future__ import annotations

import logging
from collections import defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal
from statistics import median
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, Request

from app.core.cache import features_cache, get_or_fetch, make_cache_key
from app.models import StatsGroupItem, StatsResponse
from app.services.parser_gml import parse_feature_collection
from app.services.transform import (
    _parse_doc_date,
    _safe_decimal,
    apply_local_filters,
    bbox_4326_to_2180,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/stats", tags=["stats"])


def _compute_stats(
    features: list[dict[str, str]],
) -> dict[str, Decimal | None]:
    """Compute aggregate stats from a list of property dicts."""
    prices: list[Decimal] = []
    ppsm_values: list[Decimal] = []

    for p in features:
        price = _safe_decimal(p.get("tran_cena_brutto", ""))
        area = _safe_decimal(p.get("lok_pow_uzyt", ""))
        if price is not None:
            prices.append(price)
        if price is not None and area is not None and area > 0:
            ppsm_values.append(price / area)

    result: dict[str, Decimal | None] = {
        "avg_price": None,
        "min_price": None,
        "max_price": None,
        "avg_price_per_sqm": None,
        "median_price_per_sqm": None,
    }
    if prices:
        result["avg_price"] = (sum(prices) / len(prices)).quantize(Decimal("0.01"))
        result["min_price"] = min(prices)
        result["max_price"] = max(prices)
    if ppsm_values:
        result["avg_price_per_sqm"] = (
            sum(ppsm_values) / len(ppsm_values)
        ).quantize(Decimal("0.01"))
        result["median_price_per_sqm"] = Decimal(
            str(median(ppsm_values))
        ).quantize(Decimal("0.01"))

    return result


@router.get("/lokale", response_model=StatsResponse)
async def get_lokale_stats(
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
    group_by: Annotated[
        Literal["teryt", "month"] | None,
        Query(description="Group results by teryt code or month (YYYY-MM)"),
    ] = None,
    page_size: Annotated[int, Query(ge=1, le=500)] = 500,
) -> StatsResponse:
    rcn_client = request.app.state.rcn_client

    # Convert BBOX
    bbox_2180: tuple[float, float, float, float] | None = None
    if bbox:
        parts = [float(x) for x in bbox.split(",")]
        bbox_2180 = bbox_4326_to_2180(parts[0], parts[1], parts[2], parts[3])

    cache_params = {
        "bbox_2180": bbox_2180,
        "market": market,
        "function": function,
        "count": page_size,
        "start_index": 0,
    }
    cache_key = make_cache_key(cache_params)

    try:
        xml_bytes, cache_hit = await get_or_fetch(
            features_cache,
            cache_key,
            lambda: rcn_client.get_feature(
                bbox_2180=bbox_2180,
                market=market,
                function=function,
                count=page_size,
                start_index=0,
            ),
        )
    except Exception:
        logger.exception("Upstream WFS request failed")
        raise HTTPException(
            status_code=502,
            detail="Upstream WFS service unavailable",
        )

    parsed = parse_feature_collection(xml_bytes)

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

    # Compute overall stats
    all_props = [f.properties for f in filtered]
    overall = _compute_stats(all_props)

    # Compute grouped stats if requested
    groups: list[StatsGroupItem] | None = None
    if group_by:
        buckets: dict[str, list[dict[str, str]]] = defaultdict(list)
        for f in filtered:
            p = f.properties
            if group_by == "teryt":
                key = p.get("teryt", "") or "unknown"
            else:  # month
                doc_date = _parse_doc_date(p.get("dok_data", ""))
                key = doc_date[:7] if doc_date and len(doc_date) >= 7 else "unknown"
            buckets[key].append(p)

        groups = []
        for key in sorted(buckets):
            bucket_props = buckets[key]
            bucket_stats = _compute_stats(bucket_props)
            groups.append(
                StatsGroupItem(
                    group_key=key,
                    count=len(bucket_props),
                    **bucket_stats,
                )
            )

    return StatsResponse(
        total_count=len(filtered),
        groups=groups,
        **overall,
    )
