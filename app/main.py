from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import httpx
from fastapi import FastAPI, Request, Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import settings
from app.routers import metadata, transactions
from app.services.rcn_client import RCNClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit])


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    timeout = httpx.Timeout(
        connect=settings.upstream_connect_timeout,
        read=settings.upstream_read_timeout,
        write=10.0,
        pool=10.0,
    )
    async with httpx.AsyncClient(timeout=timeout) as client:
        app.state.rcn_client = RCNClient(client)
        logger.info("RCN WFS client initialised (base_url=%s)", settings.wfs_base_url)
        yield
    logger.info("RCN WFS client shut down")


app = FastAPI(
    title="RCN Wrapper API",
    description="FastAPI wrapper for Rejestr Cen Nieruchomości (RCN) WFS service",
    version="0.1.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next) -> Response:  # type: ignore[no-untyped-def]
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response: Response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


app.include_router(transactions.router)
app.include_router(metadata.router)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "service": "RCN Wrapper API",
        "version": "0.1.0",
        "docs": "/docs",
    }
