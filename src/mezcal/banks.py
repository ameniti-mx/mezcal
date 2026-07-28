from __future__ import annotations

import re

import httpx
from lxml import html

from .constants import BANKS_URL, DEFAULT_TIMEOUT_SECONDS, DEFAULT_USER_AGENT
from .models import Bank

_CODE = re.compile(r"^\d{4,6}$")

# Respaldo deliberadamente pequeño. El catálogo vivo se consulta a Banxico y no se usa
# para rechazar códigos desconocidos, porque las instituciones cambian con el tiempo.
FALLBACK_BANKS = (
    Bank(code="40002", name="BANAMEX"),
    Bank(code="40012", name="BBVA MEXICO"),
    Bank(code="40014", name="SANTANDER"),
    Bank(code="40021", name="HSBC"),
    Bank(code="40072", name="BANORTE"),
    Bank(code="90646", name="STP"),
    Bank(code="90723", name="Cuenca"),
)


def fetch_banks(*, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> list[Bank]:
    try:
        response = httpx.get(
            BANKS_URL,
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": DEFAULT_USER_AGENT},
        )
        response.raise_for_status()
        document = html.fromstring(response.content)
        results: list[Bank] = []
        seen: set[str] = set()
        for row in document.xpath("//tr"):
            cells = [
                " ".join(cell.itertext()).strip()
                for cell in row.xpath("./th|./td")
            ]
            if len(cells) < 2:
                continue
            code, name = cells[0], cells[1]
            if _CODE.fullmatch(code) and code not in seen and name:
                seen.add(code)
                results.append(Bank(code=code, name=name))
        if results:
            return sorted(results, key=lambda bank: bank.name.casefold())
    except (httpx.HTTPError, ValueError):
        pass
    return list(FALLBACK_BANKS)


def find_banks(term: str | None = None) -> list[Bank]:
    banks = fetch_banks()
    if not term:
        return banks
    normalized = term.casefold().strip()
    return [
        bank
        for bank in banks
        if normalized in bank.name.casefold() or normalized in bank.code
    ]
