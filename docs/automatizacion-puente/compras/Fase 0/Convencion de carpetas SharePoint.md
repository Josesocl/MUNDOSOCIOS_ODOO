# Convención de carpetas y expediente de compra — SharePoint MundoSocios

**Versión:** 1.0 · **Fecha:** 2026-06-18 · **Responsable / cuenta productiva:** Patricio Fernández

## 1. Ubicación
Biblioteca **`Compras`** en el SharePoint de MundoSocios. La escritura/lectura productiva se opera con la **cuenta de Patricio Fernández** (no cuentas de consultoría).

## 2. Estructura
```
Compras/
└── {AAAA}/                         ← año
    └── {N° OC}/                    ← una carpeta por Orden de Compra
        ├── 01_Solicitud/           ← formulario Zoho (PDF/export)
        ├── 02_Cotizaciones/        ← cotizaciones recibidas
        ├── 03_OC/                  ← orden de compra emitida
        ├── 04_Factura/             ← factura del proveedor (Acepta)
        └── 05_Recepcion/           ← correo/acta de recepción conforme
```

## 3. Convención de nombres
- Carpeta de expediente: el **N° de OC de Manager+** (ej. `52800`). Mientras no exista N° OC, usar `SIN-OC_{IdSolicitudZoho}` y renombrar al emitir la OC.
- Archivos: `{N°OC}_{tipo}_{AAAA-MM-DD}.ext` (ej. `52800_Factura_2026-07-15.pdf`).

## 4. Enlace con Zoho

> **⚠️ Sin objeto (decisión del cliente, 2026-07-06):** no habrá módulo `Ordenes_Compra` en Zoho CRM. Las §1-3 (ubicación, estructura de carpetas, convención de nombres) **siguen aplicando tal cual** para organizar el respaldo documental; solo este punto §4 queda sin efecto.

~~El **link a la carpeta del expediente** se guarda en el campo `Link expediente SharePoint` del módulo `Ordenes_Compra`. Zoho **no almacena** los documentos; solo el enlace. Así el respaldo vive en SharePoint y la trazabilidad en Zoho.~~

## 5. Validación
- [ ] Se crea una carpeta de expediente de prueba con esta estructura.
- [ ] La cuenta de Patricio puede leer y escribir.
- [ ] El link pegado en Zoho abre la carpeta correcta.
