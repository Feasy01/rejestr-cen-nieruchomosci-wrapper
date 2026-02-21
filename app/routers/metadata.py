from __future__ import annotations

import logging
import time

from fastapi import APIRouter, HTTPException, Request

from app.core.cache import get_or_fetch, metadata_cache, make_cache_key
from app.models import SchemaField, SchemaResponse, UpstreamHealthResponse
from app.services.parser_gml import parse_describe_feature_type

logger = logging.getLogger(__name__)

router = APIRouter(tags=["metadata"])


@router.get("/v1/metadata/lokale/schema", response_model=SchemaResponse)
async def get_lokale_schema(request: Request) -> SchemaResponse:
    rcn_client = request.app.state.rcn_client

    cache_key = make_cache_key({"op": "describe_feature_type", "type": "ms:lokale"})

    try:
        xml_bytes, _ = await get_or_fetch(
            metadata_cache,
            cache_key,
            lambda: rcn_client.describe_feature_type("ms:lokale"),
        )
    except Exception:
        logger.exception("Failed to fetch DescribeFeatureType")
        raise HTTPException(status_code=502, detail="Upstream WFS service unavailable")

    fields_info = parse_describe_feature_type(xml_bytes)

    return SchemaResponse(
        feature_type="ms:lokale",
        fields=[
            SchemaField(name=f.name, type=f.type, min_occurs=f.min_occurs)
            for f in fields_info
        ],
    )


@router.get("/v1/health/upstream", response_model=UpstreamHealthResponse)
async def health_upstream(request: Request) -> UpstreamHealthResponse:
    rcn_client = request.app.state.rcn_client

    start = time.monotonic()
    try:
        await rcn_client.get_capabilities()
        latency_ms = (time.monotonic() - start) * 1000
        return UpstreamHealthResponse(status="ok", latency_ms=round(latency_ms, 1))
    except Exception as exc:
        latency_ms = (time.monotonic() - start) * 1000
        logger.warning("Upstream health check failed: %s", exc)
        return UpstreamHealthResponse(
            status=f"error: {type(exc).__name__}",
            latency_ms=round(latency_ms, 1),
        )
