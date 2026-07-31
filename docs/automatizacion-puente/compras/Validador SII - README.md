# Validador SII — herramienta standalone (Python)

> **Actualización 2026-07-31 (al migrar este README al repositorio):** el proveedor de verificación SII definitivo del proyecto es **SimpleAPI** (`GET https://rut.simpleapi.cl/v2/{rut}`, key contratada hasta 31-07-2027, probada en producción) — ver `herramientas/sii-simpleapi/README.md`. API Gateway y BaseAPI quedan como legado; el proxy Squid de GCP se puede apagar. Pendiente: agregar a `sii_client.py` un proveedor `simpleapi` equivalente al cliente del repo (con caché y control de cuota: 10 consultas RUT/mes) y migrar el código fuente del Validador desde el Mac al repositorio (el conector de OneDrive no lee archivos `.py`; hacerlo con git desde el clon local).

**Fecha:** 2026-07-02 · actualizado 2026-07-06 · Alternativa **fuera de Zoho**, para verificar RUT + situación tributaria contra el SII y ver el resultado en HTML. No requiere instalar nada además de Python 3 (usa solo librería estándar — sin `pip install`).

Complementa (no reemplaza) el desarrollo Deluge de `Automatizacion Puente Compras/Build/Borradores Deluge.md` (esa carpeta quedó fuera de alcance, ver banner ahí) — pero el problema de fondo (validar RUT/situación tributaria sin el sitio oficial del SII, que tiene fila y captcha) sigue vigente y esta herramienta sí se puede ejecutar y verificar con tests reales.

**Cambio de proveedor (2026-07-06):** BaseAPI (`baseapi.cl`) será discontinuada en diciembre 2026 (aviso del propio proveedor). El default ahora es **API Gateway** (`apigateway.cl`), investigado y confirmado con la documentación pública (repo oficial del cliente Python + API interna de precios del sitio). BaseAPI se mantiene como opción legado (`--proveedor baseapi`) solo mientras siga activa.

## Requisitos
- Python 3.9 o superior (viene instalado en macOS). Verificar con `python3 --version`.
- Nada más — no usa `requests`, `flask` ni ninguna librería externa.

## Modo 1 — Reporte por lote (CSV → HTML)
Para verificar muchos proveedores de una vez (por ejemplo, exportando la columna RUT de `01_Ficha_Proveedor_MundoSocios.xlsx` a CSV):

```bash
python3 cli.py --csv proveedores.csv --columna RUT --out reporte.html
```

- `--columna` es el nombre de la columna con los RUT en el CSV (default: `RUT`).
- Abrir `reporte.html` en cualquier navegador al terminar.

## Modo 2 — Formulario interactivo (uno a la vez)
Para consultar un RUT puntual desde el navegador, sin armar un CSV:

```bash
python3 server.py
```

Abrir `http://127.0.0.1:8811` en el navegador. Queda corriendo hasta apretar Ctrl+C en la terminal. **Solo accesible desde este mismo computador** (no se expone a la red).

## Probar sin credenciales reales (modo simulado)
Ambos modos aceptan `--mock`, que **no** consulta el SII de verdad — genera resultados de demostración deterministas, para probar la herramienta o mostrarla en una reunión sin depender de una cuenta de API:

```bash
python3 cli.py --rut 76123456-0 77987654-3 --out reporte.html --mock
python3 server.py --mock
```

## Modo real — configurar la API (API Gateway, default)

```bash
export APIGATEWAY_API_TOKEN="tu-token-de-api-gateway"   # Ajustes del Sistema > Panel de API Gateway
python3 cli.py --csv proveedores.csv --out reporte.html
```

Usa `GET /api/v2/sii/contribuyentes/situacion_tributaria/tercero/{rut}` — no requiere clave SII propia, solo el token de API Gateway.

**Costo real (confirmado 2026-07-06 con la API de precios pública del sitio, no una promesa de marketing):** 1 crédito = $1.000 CLP neto. El producto "Info. Contribuyentes" cuesta 10 créditos/mes fijos (~$10.000 CLP/mes) por tenerlo activo, más 0,005 créditos (~$5 CLP) por cada consulta a este endpoint. Con el volumen de MundoSocios (proveedores nuevos, no miles de consultas/mes), el costo real es prácticamente el fijo mensual.

**Importante — leer antes de usar en producción:** el endpoint, el precio y qué datos trae la respuesta están confirmados con documentación pública del proveedor (repo oficial `github.com/apigatewaycl/apigateway-api-client-python` + la API interna de precios de `apigateway.cl`). Lo que **no** está confirmado son los **nombres exactos de los campos JSON** de la respuesta (la doc pública solo los describe en prosa, no publica el schema) — no hay token de prueba real disponible para verificarlo en vivo. Antes de confiar en los resultados:
1. Crear una cuenta en API Gateway y activar el producto "Info. Contribuyentes".
2. Probar con 2-3 RUT conocidos y comparar contra lo que muestra `zeus.sii.cl/cvc/stc/stc.html` a mano.
3. Si los nombres de campo de la respuesta real difieren, ajustar `ProveedorApiGateway._parsear_respuesta` en `sii_client.py` — está aislado en un solo método para que el resto de la herramienta no se vea afectado (mismo patrón ya usado con BaseAPI).

## Modo real — BaseAPI (legado, se discontinúa dic-2026)
```bash
export SII_API_KEY="la-clave-que-entregue-baseapi"
python3 cli.py --csv proveedores.csv --out reporte.html --proveedor baseapi
```
Igual advertencia que arriba: el formato de respuesta de BaseAPI nunca se verificó con una llamada real. No usar para nada nuevo — BaseAPI deja de operar en diciembre 2026.

## Qué SÍ se automatiza y qué no
`situacion_tributaria/tercero/{rut}` de API Gateway entrega Razón Social, Giro (actividades económicas vigentes), inicio de actividades, y — nuevo respecto a BaseAPI — **observaciones de riesgo** (posible suplantación de identidad, término de giro, domicilio inexistente, etc.), visibles en una columna aparte del reporte HTML. **No** entrega Dirección ni Documentos DTE autorizados — esos 2 puntos del checklist de proveedor siguen siendo manuales (API Gateway sí los tiene en `mipyme/contribuyentes/info`, pero ese endpoint requiere la propia clave del portal SII de MundoSocios, no solo un token — evaluado y descartado por ahora, ver memoria del proyecto).

## Estructura del código
```
validador_sii/
├── rut_utils.py       # limpieza, calculo de digito verificador (Modulo 11), formato
├── sii_client.py       # cliente HTTP (ApiGateway real, BaseAPI legado, proveedor "mock" para pruebas)
├── html_report.py      # genera el reporte HTML (usado por cli.py y server.py)
├── cli.py               # modo por lote (CSV -> HTML), --proveedor {apigateway,baseapi}
├── server.py            # modo interactivo (formulario web local), --proveedor {apigateway,baseapi}
└── tests/                # 45 pruebas automatizadas, todas verificadas antes de entregar
    ├── test_rut_utils.py    # verifica el Modulo 11 contra una segunda implementacion independiente
    ├── test_sii_client.py   # levanta un servidor HTTP de prueba local para verificar ambos clientes reales
    └── test_html_report.py  # incluye pruebas de escape HTML (anti-inyeccion)
```

## Cómo se verificó (antes de entregar, no solo "se ve bien")
- **45/45 tests automatizados pasan** (`python3 -m unittest discover -s tests -v`).
- El cálculo del dígito verificador se probó contra una **segunda implementación independiente** del mismo algoritmo, para 5.000 cuerpos de RUT distintos — no se confía en pares "RUT conocido" memorizados (un primer borrador sí lo hizo y varios resultaron incorrectos al recalcular; quedó corregido).
- El cliente HTTP (BaseAPI y API Gateway) se probó contra un **servidor HTTP local real** (no solo mocks de función) — verifica que la petición, los headers y la URL/body realmente viajan por la red y se parsean bien, incluido el desenvolvimiento de `{"data": {...}}` de la API v2 de API Gateway.
- El reporte HTML se probó explícitamente contra intentos de inyección (`<script>`, `onerror=`) para confirmar que todo el contenido se escapa antes de insertarse.
- La integración completa (`server.py`) se probó levantando el servidor de verdad y haciendo una petición HTTP real con `curl`.

**Lo único que NO se pudo verificar** es el comportamiento real de ambas APIs en producción (requiere una cuenta/token real de cada una) — ver las secciones "Modo real" arriba.
