# Seguridad

## Reportar una vulnerabilidad

No publiques vulnerabilidades que expongan datos financieros en un issue público. Contacta a Ameniti mediante los canales indicados en https://ameniti.mx.

Incluye una descripción reproducible, impacto, versión afectada y una prueba completamente sintética.

## Datos sensibles

Un CEP puede contener nombres, RFC, cuentas, montos, bancos y claves de rastreo. Trátalo como información financiera confidencial.

Mezcal no debe:

- registrar cuerpos completos por defecto;
- enviar telemetría con datos de consulta;
- almacenar comprobantes sin consentimiento y controles;
- exponer una API pública sin autenticación;
- incluir secretos en imágenes Docker o repositorios.

## Despliegue

- utiliza TLS;
- configura `MEZCAL_API_KEY`;
- restringe la red de origen;
- evita logging de request bodies;
- usa almacenamiento cifrado si conservas CEP;
- elimina archivos temporales;
- limita concurrencia y frecuencia;
- mantén dependencias actualizadas.
