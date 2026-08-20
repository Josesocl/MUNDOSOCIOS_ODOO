# Portal Puente MS

Aplicación web **local** para que el equipo de MundoSocios opere el flujo de
compras y creación de proveedores **sin Terminal ni programas**: corre en un
computador (Mac o Windows) y el resto entra por el navegador en la red local.
No reemplaza a Zoho (formularios y adjuntos) ni a Manager+ (registro
contable): cubre el tramo intermedio del puente hasta Odoo.

## Qué hace

| Pestaña | Función |
|---|---|
| **Solicitudes** | Bandeja con todas las solicitudes y su estado (`INCOMPLETA / LISTA / PROCESADA / OBSERVADA`). **La aprobación por monto NO se hace aquí: viene de Zoho** (Estado de solicitud) — el portal verifica y registra |
| **Ingresar solicitud** | Se alimenta de Zoho de dos formas: **pegando** el registro del Formulario de Solicitud, o **importando** el export CSV del módulo |
| — checklist automático | Campos obligatorios · RUT válido (módulo 11) · **proveedor APTO con ficha completa** · estado de aprobación en Zoho · cotizaciones (informativo: la excepción la aprueba AyF/GG en Zoho) · saldo presupuestario del CC (aviso) |
| — registro de OC | Por solicitud: N° OC de Manager+, fecha, neto (IVA 19% y total automáticos) y carpeta del expediente (Plantilla OC) |
| **Proveedores** | Paso 1: verificación SII (SimpleAPI, registro fechado, cuota visible). Paso 2: **ficha completa del proveedor** (checklist campos críticos v2.0: identificación, representantes, DTE, datos bancarios bloqueantes, condiciones, contacto Manager+), pre-llenada con los datos del SII. Regla de avance: APTO solo con SII vigente + bancarios completos |
| — documento de carga | Para proveedor nuevo: CSV con TODOS los campos de la ficha en el orden de las pantallas de Manager+ (copia en `datos_portal/manager/`) |
| **Presupuesto** | Saldo inicial por centro de costo (los 7 CC reales de Zoho precargados); el comprometido se descuenta con las solicitudes PROCESADAS |
| **Bitácora** | Todo lo anterior, con fecha y operador |

> Cambios v2 (decisión MundoSocios 2026-08-19): se quitó la pestaña del
> TXT Banco de Chile (no se usará; la herramienta sigue aparte en
> `../validador-txt-banco`) y se quitó la aprobación por tramos de monto
> (la aprobación viene de Zoho).

## Instalación (una sola vez, en el equipo anfitrión)

1. La carpeta `portal-puente/` debe quedar **junto a** `sii-simpleapi/`
   (dentro de `herramientas/`).
2. Requiere Python 3.9+: en Mac ya viene; en Windows instalarlo desde
   python.org marcando "Add Python to PATH".
3. La API key de SimpleAPI debe estar en la variable de entorno
   `SIMPLEAPI_API_KEY` de ese equipo.

## Uso diario

- **Iniciar:** doble clic en `Iniciar_Portal.command` (Mac) o
  `Iniciar_Portal.bat` (Windows). Se abre el navegador solo.
- **Desde otros equipos de la red:** entrar a la dirección
  `http://IP-DEL-ANFITRION:8765` que la ventana muestra al iniciar.
- **Detener:** cerrar la ventana negra.

Los datos viven en `datos_portal/` (solicitudes, presupuesto, bitácora);
si la carpeta está dentro de OneDrive, queda respaldada sola.

## Reglas de negocio codificadas

- **La aprobación de la solicitud viene de Zoho**: el portal exige
  `Estado de solicitud: Aprobado` para dejarla LISTA, y solo registra la
  verificación (quién y cuándo).
- Regla de avance del proveedor (checklist v2.0): **APTO solo con
  verificación SII vigente + datos bancarios completos** (banco, tipo y
  número de cuenta, email de aviso — bloqueantes). Sin APTO no hay OC.
- Sin ambas cotizaciones: aviso con el motivo declarado (la excepción la
  aprueba AyF o la Gerencia en Zoho).
- Sin saldo presupuestario: aviso fuerte (corresponde
  ampliación/reasignación de la Gerencia).
- Los operadores se editan en `datos_portal/config.json`.

## Tests

```bash
python3 -m unittest discover tests    # 16 tests, sin red
```
