# Mezcal

**Consulta y descarga Comprobantes Electrónicos de Pago (CEP) de Banxico desde Python, terminal o una API propia.**

Mezcal es una herramienta open source impulsada por [Ameniti](https://ameniti.mx) para facilitar el acceso programático al portal público de Comprobantes Electrónicos de Pago del Banco de México.

> Mezcal es un cliente **no oficial**. No está afiliado, patrocinado ni operado por Banco de México. El portal consultado puede cambiar, limitar solicitudes o dejar de estar disponible sin previo aviso.

## ¿Qué puede hacer?

- Consultar una transferencia SPEI con los datos requeridos por Banxico.
- Interpretar el CEP XML y devolver datos normalizados.
- Descargar el comprobante en PDF, XML o ZIP.
- Usarse como biblioteca de Python.
- Usarse desde una CLI.
- Montar una API HTTP con FastAPI.
- Consultar el catálogo vigente de instituciones publicado por Banxico.
- Aplicar límites locales y autenticación opcional a la API.

## Estado

- Versión: **0.1.0**
- Estado: **alpha**
- Python: **3.10 o superior**
- Licencia: **MIT**

El portal individual de CEP no es una API pública estable. Mezcal debe considerarse una capa de integración best effort.

## Instalación

```bash
pip install mezcal-cep
```

Para usar la API:

```bash
pip install "mezcal-cep[api]"
```

Desde el código fuente:

```bash
git clone https://github.com/ameniti-mx/mezcal.git
cd mezcal
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Python

```python
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
receipt.save("./comprobantes", format="pdf")
receipt.save("./comprobantes", format="xml")
```

### Errores esperados

```python
from mezcal import (
    CEPNotAvailableError,
    RateLimitError,
    TransferNotFoundError,
    UpstreamError,
)

try:
    receipt = MezcalClient().lookup(query)
except TransferNotFoundError:
    print("No se encontró la transferencia con esos datos.")
except CEPNotAvailableError:
    print("La transferencia existe, pero el CEP todavía no está disponible.")
except RateLimitError:
    print("Se alcanzó un límite temporal de consultas.")
except UpstreamError:
    print("Banxico no está disponible o respondió de forma inesperada.")
```

## Terminal

### Consultar

```bash
mezcal consultar \
  --fecha 2026-07-27 \
  --rastreo "CLAVE-DE-RASTREO" \
  --emisor 40012 \
  --receptor 40072 \
  --cuenta 012345678901234567 \
  --monto 2500.00
```

La respuesta se imprime como JSON normalizado.

### Descargar

```bash
mezcal descargar \
  --fecha 2026-07-27 \
  --rastreo "CLAVE-DE-RASTREO" \
  --emisor 40012 \
  --receptor 40072 \
  --cuenta 012345678901234567 \
  --monto 2500.00 \
  --formato pdf \
  --salida ./comprobantes
```

Formatos disponibles: `pdf`, `xml` y `zip`.

### Instituciones

```bash
mezcal bancos
mezcal bancos --buscar bbva
mezcal bancos --buscar 90723 --json
```

El catálogo se intenta obtener del listado publicado por Banxico. Si el portal no responde, Mezcal usa un respaldo mínimo únicamente para mantener la funcionalidad básica.

## API HTTP

```bash
mezcal api --host 0.0.0.0 --port 8000
```

Documentación interactiva:

```text
http://localhost:8000/docs
```

### Consultar un CEP

```bash
curl -X POST http://localhost:8000/v1/cep/consultar \
  -H "Content-Type: application/json" \
  -d '{
    "fecha": "2026-07-27",
    "clave_rastreo": "CLAVE-DE-RASTREO",
    "emisor": "40012",
    "receptor": "40072",
    "cuenta_beneficiaria": "012345678901234567",
    "monto": {
      "value": "2500.00",
      "currency": "MXN"
    },
    "pago_a_banco": false
  }'
```

### Descargar un PDF

```bash
curl -X POST "http://localhost:8000/v1/cep/descargar?formato=pdf" \
  -H "Content-Type: application/json" \
  -d @consulta.json \
  --output comprobante.pdf
```

## Configuración de la API

| Variable | Predeterminado | Función |
|---|---:|---|
| `MEZCAL_API_KEY` | vacío | Si se configura, exige `X-API-Key`. |
| `MEZCAL_RATE_LIMIT_PER_MINUTE` | `30` | Consultas máximas por IP y minuto. |
| `MEZCAL_MAX_CONCURRENCY` | `2` | Solicitudes simultáneas hacia Banxico. |

Ejemplo:

```bash
export MEZCAL_API_KEY="cambia-esto"
export MEZCAL_RATE_LIMIT_PER_MINUTE=10
export MEZCAL_MAX_CONCURRENCY=1
mezcal api --host 0.0.0.0
```

```bash
curl http://localhost:8000/v1/bancos \
  -H "X-API-Key: cambia-esto"
```

## Docker

```bash
docker build -t mezcal .
docker run --rm -p 8000:8000 \
  -e MEZCAL_API_KEY="cambia-esto" \
  mezcal
```

O:

```bash
docker compose up --build
```

## Datos requeridos

Para descargar un CEP, Banxico solicita:

- fecha de operación;
- clave de rastreo;
- institución emisora;
- institución receptora;
- cuenta beneficiaria;
- monto exacto en MXN.

El campo `pago_a_banco` se utiliza para ciertos tipos de pago en los que la institución receptora es la beneficiaria.

## Decisiones de diseño

### El monto se recibe en pesos

Mezcal recibe `2500.00`, no `250000`. Internamente utiliza `Decimal` y expone también `minor_units` para evitar ambigüedad.

### Los códigos bancarios no se rechazan por catálogo

El catálogo de participantes cambia. Mezcal valida que el código tenga formato numérico, pero no rechaza una consulta solo porque una copia local no conozca la institución.

### Una sesión por consulta

La validación y la descarga comparten cookies y estado de sesión. Cada consulta crea una sesión independiente para evitar contaminación entre operaciones concurrentes.

### No es un proxy público ilimitado

La API incluye límites locales y concurrencia reducida. No debe exponerse públicamente sin autenticación, observabilidad y controles adicionales.

## Uso responsable

- No realices consultas masivas contra el portal individual.
- Respeta los límites y mensajes de Banxico.
- No uses la herramienta para enumerar transferencias ni probar combinaciones de datos.
- No registres cuentas, RFC, nombres completos o claves de rastreo en logs públicos.
- Trata el PDF y XML como documentos financieros con datos personales.
- Para volúmenes legítimos, evalúa el servicio de CEP por lotes de Banxico.

Consulta [`docs/responsible-use.md`](docs/responsible-use.md).

## Seguridad y privacidad

Mezcal no almacena datos por sí mismo. Una implementación de la API sí puede dejar rastros en logs, proxies, plataformas de nube o sistemas de monitoreo. Antes de desplegarla:

- desactiva el logging de cuerpos;
- usa TLS;
- configura una API key;
- evita cachés compartidas;
- establece una política de retención;
- limita el acceso a los comprobantes descargados.

Consulta [`SECURITY.md`](SECURITY.md).

## Procedencia y atribución

Mezcal está inspirado y parcialmente basado en el proyecto [`cuenca-mx/cep-python`](https://github.com/cuenca-mx/cep-python), publicado por Cuenca bajo licencia MIT.

La versión 0.1.0 conserva el aviso de copyright original y agrega una implementación ampliada por Ameniti con:

- modelos Pydantic;
- importes con `Decimal`;
- API FastAPI;
- CLI Typer;
- límites locales;
- catálogo dinámico de instituciones;
- respuestas JSON normalizadas;
- documentación de despliegue y uso responsable.

Consulta [`NOTICE`](NOTICE) y [`LICENSE`](LICENSE).

## Limitaciones

- Banxico puede cambiar el HTML, los mensajes o los endpoints.
- El portal puede exigir CAPTCHA u otros controles en el futuro.
- La disponibilidad del CEP depende de la confirmación de abono enviada por la institución receptora.
- Que no aparezca un CEP no prueba por sí mismo que el pago no exista o haya fallado.
- Mezcal no valida criptográficamente el sello del XML en esta versión.
- Mezcal no sustituye aclaraciones con instituciones financieras ni el validador oficial.

## Roadmap

### 0.1.0

- Cliente Python.
- CLI.
- API HTTP.
- PDF, XML y ZIP.
- Catálogo de instituciones.
- Límites locales y API key opcional.

### 0.2.0

- Validación criptográfica local del CEP XML.
- Adaptador para consulta por lotes.
- Caché cifrada opcional.
- Métricas OpenTelemetry.

### 0.3.0

- Webhooks para consultas diferidas.
- Persistencia opcional de trabajos.
- Panel local para operaciones autorizadas.

## Contribuir

Las contribuciones son bienvenidas. Antes de modificar el comportamiento contra Banxico, abre un issue explicando:

1. el caso de uso;
2. el volumen esperado;
3. los datos involucrados;
4. las implicaciones de privacidad;
5. cómo se evitará sobrecargar el servicio público.

Consulta [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Licencia

MIT. Consulta [`LICENSE`](LICENSE).

---

**Hecho con ❤️ por Ameniti.**
