from datetime import date
from decimal import Decimal

from mezcal import CEPQuery, MezcalClient, Money

query = CEPQuery(
    fecha=date(2026, 7, 27),
    clave_rastreo="CLAVE-DE-RASTREO",
    emisor="40012",
    receptor="40072",
    cuenta_beneficiaria="012345678901234567",
    monto=Money(value=Decimal("2500.00")),
)

receipt = MezcalClient().lookup(query)
print(receipt.to_dict())
receipt.save(".", "pdf")
