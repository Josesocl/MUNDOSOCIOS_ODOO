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

## Configuración confirmada (2026-07-31, colección Postman oficial)

Extraída de la colección Postman publicada en `documentacion.simpleapi.cl` (73 endpoints; script `extraer_endpoints_docs.py` de esta carpeta):

- **API RUT ("ObtenerDatos v2"):** `GET https://rut.simpleapi.cl/v2/{rut}` — RUT sin puntos, con guión (ej: `76192083-9`). Host propio, distinto del resto.
- **Autenticación:** header `Authorization` con la API key directa (sin `Bearer`).
- Override por si SimpleAPI cambia la URL: `export SIMPLEAPI_URL_RUT="https://.../{rut}"`.

Hosts de las demás APIs contratadas (para cuando se integren):

| API | Endpoint |
|---|---|
| DTE (generar/enviar/consultar) | `https://api.simpleapi.cl/api/v1/...` — usa Bearer token de `GET /api/auth/token` |
| RCV compras/ventas | `POST https://servicios.simpleapi.cl/api/RCV/compras/{MM}/{AAAA}` (y `/ventas/...`, también por día `{DD}/{MM}/{AAAA}`) |
| BHE Personas | `https://servicios.simpleapi.cl/api/bhe/...` (listados: `POST /api/bhe/listado/recibidas/{MM}/{AAAA}`) |
| BHE Empresas | `https://servicios.simpleapi.cl/api/bheempresas/...` |
| Folios | `POST https://servicios.simpleapi.cl/api/folios/...` |
| Mapas | `POST https://servicios.simpleapi.cl/api/mapas/...` |

**Verificado en producción (2026-07-31):** primera consulta real con el RUT de la Corporación (65.091.028-1) respondió correcto. Consumo: 1/10 del mes; la respuesta quedó en caché 90 días.

## Respuesta de la API RUT (campos confirmados) — especificación para Zoho

```json
{
  "rut": "65091028-1",
  "razonSocial": "…",
  "actividadesEconomicas": [
    {"codigo": "949903", "descripcion": "…", "categoria": "Primera",
     "afectaIVA": true, "fecha": "03-11-2014"}
  ],
  "correoIntercambio": "…",
  "domicilios": [{"direccion": "…", "ciudad": "…", "comuna": "…"}],
  "presentaInicioActividades": true,
  "fechaInicioActividades": "03-11-2014",
  "esEmpresaMenorTamano": false,
  "webFacturacion": null
}
```

Mapeo sugerido para el alta de proveedores (checklist v2.0 / módulo Zoho): `razonSocial` → razón social · `actividadesEconomicas[0].descripcion` → giro (y `codigo` → código actividad) · `afectaIVA` → afecto IVA (Nacional-factura vs Honorario-boleta) · `presentaInicioActividades` → gate del semáforo APTO (sin inicio de actividades = NO APTO) · `domicilios[0]` → dirección · `correoIntercambio` → correo SII. Fechas en formato `DD-MM-AAAA`.

## Integraciones que deben apuntar a SimpleAPI (no API Gateway)

- **Validador SII** (Mac, `Automatizacion Puente Compras/Validador SII…`): agregar proveedor `simpleapi` equivalente a este cliente; BaseAPI y API Gateway quedan como legado. El proxy Squid de GCP **ya no es necesario** (SimpleAPI es API directa con key) — se puede apagar la VM.
- **Zoho CRM** (módulo de Proveedores con Alexander Gutiérrez): la función personalizada de validación debe llamar a **SimpleAPI**, no a API Gateway. Enviarle a Alexander este README y el endpoint confirmado.

## Tests

```bash
python3 -m unittest discover tests    # 6 tests, sin red
```
