# Uso responsable

Mezcal automatiza una consulta disponible públicamente, pero eso no convierte al portal de Banxico en una API ilimitada.

## Usos apropiados

- descargar el CEP de una transferencia cuyos datos ya posee el usuario;
- integrar comprobación puntual dentro de un proceso autorizado;
- ofrecer una herramienta interna a un equipo financiero;
- obtener un comprobante a petición de una persona involucrada en el pago.

## Usos inapropiados

- probar combinaciones de cuentas, montos o claves;
- enumerar transferencias;
- construir un servicio anónimo de consultas ilimitadas;
- ignorar límites o controles del portal;
- almacenar comprobantes sin finalidad, consentimiento o medidas de seguridad;
- revender acceso al portal presentándolo como una API oficial.

## Volumen

Para múltiples transferencias, utiliza el servicio oficial de CEP por lotes cuando sea aplicable. Mezcal 0.1.0 está diseñado para consultas individuales y controladas.

## Logs

No registres cuerpos completos. Una línea segura puede contener:

```text
event=cep_lookup status=success duration_ms=842 bank_sender=40012 bank_receiver=40072
```

Evita:

- cuenta beneficiaria;
- clave de rastreo completa;
- nombre y RFC;
- monto;
- contenido PDF o XML.
