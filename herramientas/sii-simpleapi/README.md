# Conexión SII vía SimpleAPI (simpleapi.cl)

**Decisión 2026-07-31:** SimpleAPI reemplaza a API Gateway como proveedor de servicios SII del proyecto. API key contratada y vigente hasta el **31-07-2027**; los contadores se reinician el día 1 de cada mes.

## Seguridad de la API key (obligatorio)

- La key vive **solo** en la variable de entorno `SIMPLEAPI_API_KEY` (en `~/.zshrc` del equipo que ejecuta las herramientas). **Nunca** en código, documentos, planillas, correos ni chats.
- El `.gitignore` del repo excluye `.env`, `*.token` y `credentials*`.
- Si la key se llegó a compartir por un canal no seguro, **regenerarla** en el panel de SimpleAPI.

## Cuotas mensuales contratadas y su asignación en el proyecto

| API | Cuota/mes | Uso asignado en MundoSocios |
|---|---|---|
| **API RUT** | **10** | **Solo altas/cambios de proveedores** (verificación de situación tributaria del Validador). Volumen real: pocas altas/mes. La validación masiva de RUTs (socios, nóminas, devengos) es **local con módulo 11** — no gasta cuota. |
| **API DTE** | 500 | Reserva para validar facturas recibidas (recepción DTE) si se decide usarla en el puente; alcanza para el volumen mensual de facturas. |
| **API BHE Personas** | 30 | Verificación de boletas de honorarios recibidas (retención 13,75%). |
| **API BHE Empresas** | 10 | Ídem, emisor empresa. |
| **API RCV** | 30 | Cuadratura mensual del Registro de Compras y Ventas (1-2 consultas/mes reales). |
| **API Folios** | 20 | Sin uso previsto en el puente. |
| **API Mapas** | 30 | Sin uso previsto en el puente. |

**Regla de oro:** con 10 consultas RUT/mes, toda consulta pasa por el cliente de esta carpeta, que **cachea 90 días y bloquea al llegar al límite**. Prohibido llamar la API directo desde planillas o scripts sueltos.

## Cliente (`cliente_simpleapi.py`)

```bash
export SIMPLEAPI_API_KEY="....."
python3 cliente_simpleapi.py --rut 76123456-7      # consulta (cache → API)
python3 cliente_simpleapi.py --estado              # cuota usada del mes
python3 cliente_simpleapi.py --rut ... --mock      # prueba sin red ni cuota
```

Protecciones incorporadas: RUT validado con módulo 11 antes de gastar cuota · caché en disco 90 días · contador mensual con bloqueo (y `--forzar` explícito) · errores con mensaje claro (sin key, cuota agotada, HTTP).

## ⚠️ Pendiente de confirmar (primera ejecución real, desde el Mac)

La red del entorno donde se escribió este cliente bloquea `simpleapi.cl`, así que **la URL del endpoint y la cabecera de autenticación están como valores por defecto razonables y deben confirmarse** contra la documentación oficial (`documentacion.simpleapi.cl`):

1. `SIMPLEAPI_BASE_URL` (default `https://servicios.simpleapi.cl`)
2. `SIMPLEAPI_RUTA_RUT` (default `/api/RUT/{rut}`)
3. `SIMPLEAPI_CABECERA_AUTH` (default `Authorization`)

Si difieren, se ajustan por variable de entorno sin tocar el código. Primera prueba sugerida: 2 RUTs conocidos (uno vigente y el de la Corporación) y comparar contra `zeus.sii.cl` — gasta 2 de las 10 consultas del mes.

## Integraciones que deben apuntar a SimpleAPI (no API Gateway)

- **Validador SII** (Mac, `Automatizacion Puente Compras/Validador SII…`): agregar proveedor `simpleapi` equivalente a este cliente; BaseAPI y API Gateway quedan como legado. El proxy Squid de GCP **ya no es necesario** (SimpleAPI es API directa con key) — se puede apagar la VM.
- **Zoho CRM** (módulo de Proveedores con Alexander Gutiérrez): la función personalizada de validación debe llamar a **SimpleAPI**, no a API Gateway. Enviarle a Alexander este README y el endpoint confirmado.

## Tests

```bash
python3 -m unittest discover tests    # 6 tests, sin red
```
