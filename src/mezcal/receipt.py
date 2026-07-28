from __future__ import annotations

from pathlib import Path

from .constants import DownloadFormat
from .models import CEPQuery, Transfer


class CEPReceipt:
    """Resultado validado, ligado a la sesión que permite descargar el CEP."""

    def __init__(self, *, query: CEPQuery, transfer: Transfer, session: object) -> None:
        self.query = query
        self.transfer = transfer
        self._session = session

    def to_dict(self) -> dict[str, object]:
        return self.transfer.public_dict()

    def download(self, format: str | DownloadFormat = DownloadFormat.PDF) -> bytes:
        parsed = format if isinstance(format, DownloadFormat) else DownloadFormat.parse(format)
        downloader = getattr(self._session, "download")
        return downloader(parsed)

    def save(
        self,
        destination: str | Path,
        format: str | DownloadFormat = DownloadFormat.PDF,
    ) -> Path:
        parsed = format if isinstance(format, DownloadFormat) else DownloadFormat.parse(format)
        path = Path(destination)
        if path.is_dir():
            safe_key = "".join(
                char if char.isalnum() or char in "-_" else "_"
                for char in self.query.clave_rastreo
            )
            path = path / f"CEP-{self.query.fecha.isoformat()}-{safe_key}.{parsed.extension}"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.download(parsed))
        return path
