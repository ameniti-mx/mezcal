from __future__ import annotations

import html
from dataclasses import dataclass
from typing import Any

import httpx

from .constants import (
    BASE_URL,
    BETA_BASE_URL,
    DEFAULT_TIMEOUT_SECONDS,
    DEFAULT_USER_AGENT,
    DownloadFormat,
    MAX_REQUEST_MARKERS,
    NOT_AVAILABLE_MARKERS,
    NOT_FOUND_MARKERS,
)
from .errors import (
    CEPNotAvailableError,
    RateLimitError,
    TransferNotFoundError,
    UpstreamError,
)
from .models import CEPQuery
from .parser import parse_cep_xml
from .receipt import CEPReceipt


@dataclass
class _ValidatedSession:
    client: httpx.Client
    base_url: str

    def download(self, format: DownloadFormat) -> bytes:
        try:
            response = self.client.get(
                f"{self.base_url}/descarga.do",
                params={"formato": format.value},
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise UpstreamError("No fue posible descargar el CEP desde Banxico.") from exc
        return response.content

    def close(self) -> None:
        self.client.close()


class MezcalClient:
    """Cliente no oficial para el portal individual de CEP de Banco de México."""

    def __init__(
        self,
        *,
        beta: bool = False,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        user_agent: str = DEFAULT_USER_AGENT,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = BETA_BASE_URL if beta else BASE_URL
        self.timeout = timeout
        self.user_agent = user_agent
        self.transport = transport

    def _new_http_client(self) -> httpx.Client:
        return httpx.Client(
            timeout=self.timeout,
            follow_redirects=True,
            headers={
                "User-Agent": self.user_agent,
                "Accept-Language": "es-MX,es;q=0.9",
            },
            transport=self.transport,
        )

    @staticmethod
    def _normalize_page(content: bytes) -> str:
        return html.unescape(content.decode("utf-8", errors="replace"))

    @staticmethod
    def _contains_any(text: str, markers: tuple[str, ...]) -> bool:
        lowered = text.casefold()
        return any(html.unescape(marker).casefold() in lowered for marker in markers)

    def lookup(self, query: CEPQuery | dict[str, Any]) -> CEPReceipt:
        parsed_query = query if isinstance(query, CEPQuery) else CEPQuery.model_validate(query)
        client = self._new_http_client()
        validated = _ValidatedSession(client=client, base_url=self.base_url)
        try:
            response = client.post(
                f"{self.base_url}/valida.do",
                data=parsed_query.banxico_payload(),
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            client.close()
            if exc.response.status_code == 429:
                raise RateLimitError(
                    "Banxico limitó temporalmente el número de consultas."
                ) from exc
            raise UpstreamError(
                f"Banxico respondió HTTP {exc.response.status_code}."
            ) from exc
        except httpx.HTTPError as exc:
            client.close()
            raise UpstreamError("No fue posible comunicarse con Banxico.") from exc

        page = self._normalize_page(response.content)
        if self._contains_any(page, MAX_REQUEST_MARKERS):
            client.close()
            raise RateLimitError(
                "Banxico informó que se alcanzó el máximo temporal de consultas."
            )
        if self._contains_any(page, NOT_AVAILABLE_MARKERS):
            client.close()
            raise CEPNotAvailableError(
                "La transferencia fue identificada, pero el CEP aún no está disponible."
            )
        if self._contains_any(page, NOT_FOUND_MARKERS):
            client.close()
            raise TransferNotFoundError(
                "No se encontró una transferencia con los datos proporcionados."
            )

        try:
            xml = validated.download(DownloadFormat.XML)
            transfer = parse_cep_xml(xml, parsed_query)
        except Exception:
            client.close()
            raise
        return CEPReceipt(query=parsed_query, transfer=transfer, session=validated)
