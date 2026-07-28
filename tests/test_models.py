from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from mezcal.models import CEPQuery, Money


def test_money_uses_decimal_and_minor_units() -> None:
    money = Money(value="1234.5")
    assert money.value == Decimal("1234.50")
    assert money.minor_units == 123450


def test_query_generates_banxico_payload() -> None:
    query = CEPQuery(
        fecha=date(2026, 7, 27),
        clave_rastreo="TRACK-001",
        emisor="40012",
        receptor="40072",
        cuenta_beneficiaria="012345678901234567",
        monto=Money(value="2500.00"),
    )
    payload = query.banxico_payload()
    assert payload["fecha"] == "27-07-2026"
    assert payload["monto"] == "2500.00"
    assert payload["receptorParticipante"] == 0


def test_rejects_invalid_bank_code() -> None:
    with pytest.raises(ValidationError):
        CEPQuery(
            fecha=date(2026, 7, 27),
            clave_rastreo="TRACK-001",
            emisor="BBVA",
            receptor="40072",
            cuenta_beneficiaria="012345678901234567",
            monto=Money(value="1.00"),
        )
