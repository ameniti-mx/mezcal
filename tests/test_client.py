from datetime import date
from pathlib import Path

import httpx
import pytest

from mezcal import CEPQuery, MezcalClient, Money
from mezcal.errors import (
    CEPNotAvailableError,
    RateLimitError,
    TransferNotFoundError,
)

XML = (Path(__file__).parent / "fixtures" / "cep.xml").read_bytes()


def query() -> CEPQuery:
    return CEPQuery(
        fecha=date(2026, 7, 27),
        clave_rastreo="TRACK-001",
        emisor="40012",
        receptor="40072",
        cuenta_beneficiaria="012345678901234567",
        monto=Money(value="2500.00"),
    )


def test_lookup_and_download_share_session() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.url.path.endswith("/valida.do"):
            return httpx.Response(200, content=b"consulta aceptada")
        if request.url.path.endswith("/descarga.do"):
            fmt = request.url.params.get("formato")
            return httpx.Response(200, content=XML if fmt == "XML" else b"PDF")
        raise AssertionError(request.url)

    client = MezcalClient(transport=httpx.MockTransport(handler))
    receipt = client.lookup(query())
    assert receipt.transfer.tipo_pago == 1
    assert receipt.download("pdf") == b"PDF"
    assert calls == [
        "/cep/valida.do",
        "/cep/descarga.do",
        "/cep/descarga.do",
    ]


@pytest.mark.parametrize(
    ("body", "error"),
    [
        ("No se encontró ningún pago con la información proporcionada", TransferNotFoundError),
        ("Con la información proporcionada se identificó el siguiente pago", CEPNotAvailableError),
        ("Ha excedido el número máximo de consultas", RateLimitError),
    ],
)
def test_maps_portal_messages(body: str, error: type[Exception]) -> None:
    transport = httpx.MockTransport(lambda _: httpx.Response(200, text=body))
    with pytest.raises(error):
        MezcalClient(transport=transport).lookup(query())
