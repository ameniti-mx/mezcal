from __future__ import annotations

import asyncio
import os
import time
from collections import defaultdict, deque
from typing import Annotated

from fastapi import Depends, FastAPI, Header, Query, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse, Response

from . import __version__
from .banks import find_banks
from .client import MezcalClient
from .constants import DownloadFormat
from .errors import MezcalError, RateLimitError
from .models import CEPQuery

app = FastAPI(
    title="Mezcal",
    version=__version__,
    description=(
        "API no oficial para consultar y descargar Comprobantes Electrónicos de "
        "Pago (CEP) desde el portal público de Banco de México."
    ),
)

_API_KEY = os.getenv("MEZCAL_API_KEY")
_RATE_LIMIT = max(1, int(os.getenv("MEZCAL_RATE_LIMIT_PER_MINUTE", "30")))
_MAX_CONCURRENCY = max(1, int(os.getenv("MEZCAL_MAX_CONCURRENCY", "2")))
_request_history: dict[str, deque[float]] = defaultdict(deque)
_history_lock = asyncio.Lock()
_upstream_semaphore = asyncio.Semaphore(_MAX_CONCURRENCY)


async def authorize(x_api_key: Annotated[str | None, Header()] = None) -> None:
    if _API_KEY and x_api_key != _API_KEY:
        from fastapi import HTTPException

        raise HTTPException(status_code=401, detail="API key inválida o ausente.")


async def rate_limit(request: Request) -> None:
    identity = request.client.host if request.client else "unknown"
    now = time.monotonic()
    async with _history_lock:
        history = _request_history[identity]
        while history and now - history[0] >= 60:
            history.popleft()
        if len(history) >= _RATE_LIMIT:
            raise RateLimitError("Límite local de consultas por minuto alcanzado.")
        history.append(now)


@app.exception_handler(MezcalError)
async def mezcal_error_handler(_: Request, exc: MezcalError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.http_status,
        content={"error": {"code": exc.code, "message": str(exc)}},
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "mezcal", "version": __version__}


@app.get("/v1/bancos", dependencies=[Depends(authorize)])
async def banks(q: str | None = None) -> dict[str, object]:
    results = await run_in_threadpool(find_banks, q)
    return {"data": [bank.model_dump() for bank in results]}


async def _lookup(query: CEPQuery):
    async with _upstream_semaphore:
        return await run_in_threadpool(MezcalClient().lookup, query)


@app.post(
    "/v1/cep/consultar",
    dependencies=[Depends(authorize), Depends(rate_limit)],
)
async def lookup(query: CEPQuery) -> dict[str, object]:
    receipt = await _lookup(query)
    return {"data": receipt.to_dict()}


@app.post(
    "/v1/cep/descargar",
    dependencies=[Depends(authorize), Depends(rate_limit)],
)
async def download(
    query: CEPQuery,
    formato: Annotated[str, Query(pattern="^(?i:pdf|xml|zip)$")] = "pdf",
) -> Response:
    parsed = DownloadFormat.parse(formato)
    receipt = await _lookup(query)
    content = await run_in_threadpool(receipt.download, parsed)
    safe_key = "".join(
        char if char.isalnum() or char in "-_" else "_"
        for char in query.clave_rastreo
    )
    filename = f"CEP-{query.fecha.isoformat()}-{safe_key}.{parsed.extension}"
    return Response(
        content=content,
        media_type=parsed.media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
