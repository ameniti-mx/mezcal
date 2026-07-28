from __future__ import annotations

from enum import StrEnum

BASE_URL = "https://www.banxico.org.mx/cep"
BETA_BASE_URL = "https://www.banxico.org.mx/cep-beta"
BANKS_URL = "https://www.banxico.org.mx/cep-scl/listaInstituciones.do"

DEFAULT_TIMEOUT_SECONDS = 20.0
DEFAULT_USER_AGENT = (
    "Mezcal/0.1.0 (+https://github.com/ameniti-mx/mezcal; "
    "consulta responsable de CEP)"
)

MAX_REQUEST_MARKERS = (
    "ha excedido el número máximo de consultas",
    "ha excedido el n&uacute;mero m&aacute;ximo de consultas",
)
NOT_FOUND_MARKERS = (
    "No se encontró ningún pago con la información proporcionada",
    "El SPEI no ha recibido una orden de pago que cumpla con el criterio",
    "Operación no encontrada",
)
NOT_AVAILABLE_MARKERS = (
    "Con la información proporcionada se identificó el siguiente pago",
    "institución receptora de la transferencia aún no realiza la Confirmación",
)


class DownloadFormat(StrEnum):
    PDF = "PDF"
    XML = "XML"
    ZIP = "ZIP"

    @classmethod
    def parse(cls, value: str) -> "DownloadFormat":
        try:
            return cls(value.upper())
        except ValueError as exc:
            supported = ", ".join(item.value.lower() for item in cls)
            raise ValueError(f"Formato inválido. Usa: {supported}.") from exc

    @property
    def extension(self) -> str:
        return self.value.lower()

    @property
    def media_type(self) -> str:
        return {
            self.PDF: "application/pdf",
            self.XML: "application/xml",
            self.ZIP: "application/zip",
        }[self]
