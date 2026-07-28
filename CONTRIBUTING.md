# Contribuir a Mezcal

Gracias por ayudar a mejorar Mezcal.

## Principios

1. **Uso responsable:** ningún cambio debe fomentar enumeración, abuso o consultas masivas contra Banxico.
2. **Privacidad:** no publiques CEP, claves de rastreo, cuentas, RFC, nombres o montos reales.
3. **Compatibilidad:** conserva la API pública o documenta claramente los cambios incompatibles.
4. **Pruebas offline:** las pruebas automatizadas deben utilizar fixtures sintéticos y transports simulados.
5. **Atribución:** no elimines los avisos de Cuenca ni Ameniti.

## Desarrollo

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
ruff check .
mypy src/mezcal
```

## Issues

Incluye:

- descripción del problema;
- comportamiento esperado;
- versión de Python;
- respuesta sanitizada;
- impacto de privacidad;
- volumen de solicitudes esperado.

## Pull requests

- agrega o actualiza pruebas;
- actualiza `CHANGELOG.md`;
- evita nuevas dependencias salvo que sean necesarias;
- no incluyas información financiera real;
- explica cualquier cambio a endpoints o parámetros de Banxico.
