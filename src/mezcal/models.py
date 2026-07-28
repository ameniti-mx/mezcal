from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

BANK_CODE_RE = re.compile(r"^\d{4,6}$")
ACCOUNT_RE = re.compile(r"^[A-Za-z0-9]{10,20}$")
TRACKING_RE = re.compile(r"^[A-Za-z0-9._\- ]{1,40}$")


class Money(BaseModel):
    model_config = ConfigDict(frozen=True)

    value: Decimal = Field(gt=Decimal("0"), decimal_places=2)
    currency: str = "MXN"

    @field_validator("value", mode="before")
    @classmethod
    def normalize_value(cls, value: Any) -> Decimal:
        try:
            decimal_value = Decimal(str(value)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        except (InvalidOperation, ValueError) as exc:
            raise ValueError("El monto debe ser un número decimal válido.") from exc
        if decimal_value <= 0:
            raise ValueError("El monto debe ser mayor que cero.")
        return decimal_value

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        value = value.upper().strip()
        if value != "MXN":
            raise ValueError("La consulta CEP de SPEI utiliza moneda MXN.")
        return value

    @property
    def minor_units(self) -> int:
        return int(self.value * 100)


class CEPQuery(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, frozen=True)

    fecha: date
    clave_rastreo: str = Field(min_length=1, max_length=40)
    emisor: str
    receptor: str
    cuenta_beneficiaria: str = Field(min_length=10, max_length=20)
    monto: Money
    pago_a_banco: bool = False

    @field_validator("clave_rastreo")
    @classmethod
    def validate_tracking_key(cls, value: str) -> str:
        value = value.strip()
        if not TRACKING_RE.fullmatch(value):
            raise ValueError(
                "La clave de rastreo contiene caracteres no admitidos o es demasiado larga."
            )
        return value

    @field_validator("emisor", "receptor")
    @classmethod
    def validate_bank_code(cls, value: str) -> str:
        value = value.strip()
        if not BANK_CODE_RE.fullmatch(value):
            raise ValueError("La clave de institución debe contener entre 4 y 6 dígitos.")
        return value

    @field_validator("cuenta_beneficiaria")
    @classmethod
    def validate_account(cls, value: str) -> str:
        value = re.sub(r"\s+", "", value)
        if not ACCOUNT_RE.fullmatch(value):
            raise ValueError(
                "La cuenta beneficiaria debe contener de 10 a 20 caracteres alfanuméricos."
            )
        return value

    def banxico_payload(self) -> dict[str, str | int]:
        return {
            "tipoCriterio": "T",
            "captcha": "c",
            "tipoConsulta": 1,
            "fecha": self.fecha.strftime("%d-%m-%Y"),
            "criterio": self.clave_rastreo,
            "emisor": self.emisor,
            "receptor": self.receptor,
            "cuenta": self.cuenta_beneficiaria,
            "monto": format(self.monto.value, ".2f"),
            "receptorParticipante": 1 if self.pago_a_banco else 0,
        }


class Account(BaseModel):
    model_config = ConfigDict(frozen=True)

    nombre: str = "NA"
    tipo_cuenta: str = "NA"
    banco: str = "NA"
    numero: str = "NA"
    rfc: str = "NA"


class Transfer(BaseModel):
    model_config = ConfigDict(frozen=True)

    fecha_operacion: date
    fecha_abono: datetime | None = None
    ordenante: Account
    beneficiario: Account
    monto: Money
    iva: Decimal = Decimal("0.00")
    concepto: str = ""
    clave_rastreo: str
    emisor: str
    receptor: str
    sello: str = ""
    numero_certificado: str | None = None
    cadena_original: str | None = None
    tipo_pago: int | None = None
    pago_a_banco: bool = False
    xml_sha256: str

    def public_dict(self) -> dict[str, Any]:
        data = self.model_dump(mode="json")
        data["monto"]["minor_units"] = self.monto.minor_units
        return data


class Bank(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str
    name: str
