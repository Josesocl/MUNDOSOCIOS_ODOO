# Portal Puente MS

Aplicación web **local** para que el equipo de MundoSocios opere el flujo de
compras y creación de proveedores **sin Terminal ni programas**: corre en un
computador (Mac o Windows) y el resto entra por el navegador en la red local.
No reemplaza a Zoho (formularios y adjuntos) ni a Manager+ (registro
contable): cubre el tramo intermedio del puente hasta Odoo.

## Qué hace

| Pestaña | Función |
|---|---|
| **Solicitudes** | Bandeja con todas las solicitudes y su estado (`INCOMPLETA / LISTA / APROBADA / APROBADA-EXCEPCION / RECHAZADA`) |
| **Ingresar solicitud** | Se alimenta de Zoho de dos formas: **pegando** el registro del Formulario de Solicitud, o **importando** el export CSV del módulo |
| — checklist automático | Campos obligatorios · RUT válido (módulo 11) · proveedor APTO-SII · tramo y aprobador según la **matriz vigente de 4 tramos** · cotizaciones (sin ambas → solo aprueba **Adm. y Finanzas o Gerencia General**) · saldo presupuestario del CC (sin saldo → solo **Gerencia**) |
| **Proveedores** | Verificación SII vía SimpleAPI con registro fechado y cuota visible (usa `../sii-simpleapi`) |
| **Presupuesto** | Saldo inicial por centro de costo (los 7 CC reales de Zoho precargados); el comprometido se descuenta solo con cada aprobación |
| Archivo Manager+ | En cada solicitud aprobada: botón para descargar el CSV con los datos del proveedor y de la OC en el orden de las pantallas de Manager+ |
| **TXT banco** | Validación del TXT de nómina y corrección de fecha de pago (usa `../validador-txt-banco`) |
| **Bitácora** | Todo lo anterior, con fecha y operador |

## Instalación (una sola vez, en el equipo anfitrión)

1. La carpeta `portal-puente/` debe quedar **junto a** `sii-simpleapi/` y
   `validador-txt-banco/` (dentro de `herramientas/`).
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

- Matriz de aprobación vigente (CLP c/IVA): ≤$500K dueño del presupuesto ·
  ≤$1M Cecilia Ramírez · ≤$5M Patricio Fernández · >$5M Patricio +
  Constanza (BP Flujo Compras v2.2 §2.5 — en Odoo cambia al esquema UF).
- Sin ambas cotizaciones la solicitud **no se rechaza**: requiere
  aprobación de excepción (roles AYF o GG), con el motivo declarado visible.
- Sin saldo presupuestario solo la Gerencia aprueba
  (ampliación/reasignación), según los flujos PF 2026-08.
- Ningún proveedor NO APTO (o sin verificación SII) pasa a OC.
- Los operadores y sus roles se editan en `datos_portal/config.json`
  (roles: OPERADOR, COMPRAS, AYF, GG).

## Tests

```bash
python3 -m unittest discover tests    # 13 tests, sin red
```
