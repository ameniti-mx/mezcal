from datetime import date, datetime
from pathlib import Path

from mezcal.models import CEPQuery, Money
from mezcal.parser import parse_cep_xml

FIXTURE = Path(__file__).parent / "fixtures" / "cep.xml"


def test_parses_cep_xml() -> None:
    query = CEPQuery(
        fecha=date(2026, 7, 27),
        clave_rastreo="TRACK-001",
        emisor="40012",
        receptor="40072",
        cuenta_beneficiaria="012345678901234567",
        monto=Money(value="2500.00"),
    )
    transfer = parse_cep_xml(FIXTURE.read_bytes(), query)
    assert transfer.fecha_operacion == date(2026, 7, 27)
    assert transfer.fecha_abono == datetime(2026, 7, 27, 10, 30, 45)
    assert transfer.tipo_pago == 1
    assert transfer.beneficiario.banco == "40072"
    assert transfer.beneficiario.numero == "012345678901234567"
    assert transfer.monto.minor_units == 250000
    assert len(transfer.xml_sha256) == 64
