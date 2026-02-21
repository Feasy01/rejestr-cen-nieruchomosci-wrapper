from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field


class GeoJSONPoint(BaseModel):
    type: Literal["Point"] = "Point"
    coordinates: list[float] = Field(
        ..., description="[longitude, latitude] in EPSG:4326"
    )


class TransactionItem(BaseModel):
    id: str
    doc_date: str | None = None
    doc_ref: str | None = None
    notary: str | None = None
    market: str | None = None
    price_brutto: Decimal | None = None
    area_uzyt: Decimal | None = None
    function: str | None = None
    rooms: int | None = None
    floor: str | None = None
    share: str | None = None
    geometry: GeoJSONPoint | None = None
    raw: dict[str, Any] | None = None
    source: str = "geoportal_rcn_wfs"
    fetched_at: datetime


class TransactionListResponse(BaseModel):
    page: int
    page_size: int
    next_page: int | None = None
    items: list[TransactionItem]


class SchemaField(BaseModel):
    name: str
    type: str
    min_occurs: int = 0


class SchemaResponse(BaseModel):
    feature_type: str
    fields: list[SchemaField]


class UpstreamHealthResponse(BaseModel):
    status: str
    latency_ms: float


class ErrorResponse(BaseModel):
    detail: str
