from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from .banks import find_banks
from .client import MezcalClient
from .constants import DownloadFormat
from .errors import MezcalError
from .models import CEPQuery, Money

app = typer.Typer(
    name="mezcal",
    help="Consulta y descarga Comprobantes Electrónicos de Pago (CEP) de Banxico.",
    no_args_is_help=True,
)
console = Console()


def _query(
    fecha: str,
    clave_rastreo: str,
    emisor: str,
    receptor: str,
    cuenta: str,
    monto: str,
    pago_a_banco: bool,
) -> CEPQuery:
    return CEPQuery(
        fecha=date.fromisoformat(fecha),
        clave_rastreo=clave_rastreo,
        emisor=emisor,
        receptor=receptor,
        cuenta_beneficiaria=cuenta,
        monto=Money(value=Decimal(monto)),
        pago_a_banco=pago_a_banco,
    )


def _handle_error(exc: Exception) -> None:
    if isinstance(exc, MezcalError):
        console.print(f"[bold red]{exc.code}:[/bold red] {exc}")
        raise typer.Exit(code={404: 3, 409: 4, 429: 5}.get(exc.http_status, 1))
    console.print(f"[bold red]error:[/bold red] {exc}")
    raise typer.Exit(code=1)


@app.command()
def version() -> None:
    """Muestra la versión instalada."""
    console.print(__version__)


@app.command("consultar")
def lookup(
    fecha: Annotated[str, typer.Option(help="Fecha de operación: AAAA-MM-DD")],
    clave_rastreo: Annotated[str, typer.Option("--rastreo", help="Clave de rastreo")],
    emisor: Annotated[str, typer.Option(help="Clave de institución emisora")],
    receptor: Annotated[str, typer.Option(help="Clave de institución receptora")],
    cuenta: Annotated[str, typer.Option(help="Cuenta beneficiaria")],
    monto: Annotated[str, typer.Option(help="Monto en pesos, por ejemplo 1250.50")],
    pago_a_banco: Annotated[
        bool, typer.Option("--pago-a-banco", help="Pagos de tipos 4 o 31")
    ] = False,
    beta: Annotated[bool, typer.Option(help="Usa el portal beta de Banxico")] = False,
    pretty: Annotated[bool, typer.Option(help="JSON indentado")] = True,
) -> None:
    """Consulta un CEP y devuelve sus datos normalizados en JSON."""
    try:
        receipt = MezcalClient(beta=beta).lookup(
            _query(fecha, clave_rastreo, emisor, receptor, cuenta, monto, pago_a_banco)
        )
        console.print_json(
            json.dumps(receipt.to_dict(), ensure_ascii=False, indent=2 if pretty else None)
        )
    except Exception as exc:
        _handle_error(exc)


@app.command("descargar")
def download(
    fecha: Annotated[str, typer.Option(help="Fecha de operación: AAAA-MM-DD")],
    clave_rastreo: Annotated[str, typer.Option("--rastreo", help="Clave de rastreo")],
    emisor: Annotated[str, typer.Option(help="Clave de institución emisora")],
    receptor: Annotated[str, typer.Option(help="Clave de institución receptora")],
    cuenta: Annotated[str, typer.Option(help="Cuenta beneficiaria")],
    monto: Annotated[str, typer.Option(help="Monto en pesos")],
    formato: Annotated[str, typer.Option(help="pdf, xml o zip")] = "pdf",
    salida: Annotated[Path, typer.Option(help="Archivo o directorio de salida")] = Path("."),
    pago_a_banco: Annotated[bool, typer.Option("--pago-a-banco")] = False,
    beta: Annotated[bool, typer.Option()] = False,
) -> None:
    """Descarga el CEP en PDF, XML o ZIP."""
    try:
        parsed_format = DownloadFormat.parse(formato)
        receipt = MezcalClient(beta=beta).lookup(
            _query(fecha, clave_rastreo, emisor, receptor, cuenta, monto, pago_a_banco)
        )
        path = receipt.save(salida, parsed_format)
        console.print(f"[bold green]CEP guardado:[/bold green] {path}")
    except Exception as exc:
        _handle_error(exc)


@app.command("bancos")
def banks(
    buscar: Annotated[str | None, typer.Option(help="Nombre o clave")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Salida JSON")] = False,
) -> None:
    """Consulta el catálogo vigente de instituciones publicado por Banxico."""
    results = find_banks(buscar)
    if json_output:
        console.print_json(
            json.dumps([item.model_dump() for item in results], ensure_ascii=False)
        )
        return
    table = Table(title="Instituciones financieras")
    table.add_column("Clave", style="cyan")
    table.add_column("Institución")
    for item in results:
        table.add_row(item.code, item.name)
    console.print(table)


@app.command("api")
def serve_api(
    host: Annotated[str, typer.Option()] = "127.0.0.1",
    port: Annotated[int, typer.Option()] = 8000,
    reload: Annotated[bool, typer.Option()] = False,
) -> None:
    """Monta la API HTTP de Mezcal con FastAPI."""
    try:
        import uvicorn
    except ImportError as exc:
        console.print(
            "Instala el extra de API: [bold]pip install 'mezcal-cep[api]'[/bold]"
        )
        raise typer.Exit(code=1) from exc
    uvicorn.run("mezcal.api:app", host=host, port=port, reload=reload)
