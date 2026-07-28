# Arquitectura

## Flujo de consulta

1. El consumidor construye un `CEPQuery`.
2. Pydantic normaliza y valida formatos básicos.
3. `MezcalClient` crea una sesión HTTP independiente.
4. La sesión envía los datos al formulario individual de Banxico.
5. Mezcal interpreta los mensajes de estado devueltos.
6. Si el CEP está disponible, descarga el XML con la misma sesión.
7. `parse_cep_xml` transforma el XML en un modelo `Transfer`.
8. `CEPReceipt` conserva la sesión para descargar PDF, XML o ZIP.

## Componentes

- `models.py`: contratos públicos de datos.
- `client.py`: interacción HTTP con el portal.
- `parser.py`: lectura segura del XML.
- `receipt.py`: descarga y persistencia local.
- `banks.py`: catálogo público de instituciones.
- `cli.py`: interfaz de terminal.
- `api.py`: interfaz HTTP opcional.

## Concurrencia

Cada consulta utiliza su propia sesión porque la descarga depende de cookies y estado generado por la validación. La API limita de forma predeterminada las solicitudes concurrentes hacia Banxico a dos.

## Fallos

Los fallos se expresan mediante excepciones públicas estables:

- `TransferNotFoundError`;
- `CEPNotAvailableError`;
- `RateLimitError`;
- `UpstreamError`;
- `ParseError`.

La API convierte estas excepciones en respuestas JSON con códigos HTTP previsibles.
