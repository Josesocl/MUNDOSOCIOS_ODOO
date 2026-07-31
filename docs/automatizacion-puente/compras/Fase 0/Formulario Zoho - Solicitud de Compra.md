# Formulario "Solicitud de Compra" — Zoho Forms (campo por campo)

> **⚠️ FUERA DE ALCANCE (decisión del cliente, 2026-07-06):** no se construirá en Zoho Forms/CRM. Referencia histórica. La **tabla de campos obligatorios (más abajo)** sigue siendo útil como checklist de qué debe traer toda solicitud de compra por el canal que se use hoy (correo/formulario existente), independiente de la herramienta.

**Fecha:** 2026-06-18 · revisado 2026-07-02 para coherencia con `Build/Blueprint - Proceso Compras y Proveedores.md`.
Construir en Zoho Forms y mapear al módulo `Solicitudes` (CRM).
Objetivo: que ninguna solicitud entre incompleta (hoy es la causa principal de rechazo y retrabajo).

## Campos del formulario

| # | Etiqueta visible | Tipo Zoho Forms | Obligatorio | Validación / ayuda | Campo CRM destino |
|---|---|---|---|---|---|
| 1 | Solicitante | Single Line / Email | Sí | Autollenar con usuario | Solicitante |
| 2 | Área / centro de costo | Dropdown | Sí | Lista de centros de costo | Centro de costo |
| 3 | Línea de negocio / proyecto | Dropdown | No | Solo si aplica | (campo opcional) |
| 4 | Cuenta contable | Dropdown | Sí | Lista de cuentas | Cuenta contable |
| 5 | Descripción del bien/servicio | Multi Line | Sí | Qué se necesita y para qué | Descripción |
| 6 | Cantidad | Number | Sí | > 0 | Cantidad |
| 7 | Fecha requerida | Date | Sí | No anterior a hoy | Fecha requerida |
| 8 | Presupuesto estimado (CLP) | Number/Currency | Sí | Monto bruto estimado | Presupuesto estimado |
| 9 | Proveedor sugerido | Lookup (buscar en `Proveedores`) | No | Si lo hay — **no** texto libre, para que quede conectado a la Ficha de Proveedor real y su Estado (Apto/En validación) | Proveedor sugerido |
| 10 | Motivo de selección del proveedor | Multi Line | Condicional | Obligatorio si hay proveedor sugerido | Motivo de selección |
| 11 | Cotizaciones (adjunto) | File Upload | No* | PDF/imagen; múltiples | (a Cotizaciones) |
| 12 | Observaciones | Multi Line | No | | (notas) |

\* No obligatorio al enviar, pero la solicitud no avanza de "Cotización" sin al menos una cotización cargada (regla del Blueprint).

## Reglas del formulario
- **Campos condicionales:** el campo 10 (motivo) se vuelve obligatorio si el 9 (proveedor sugerido) tiene valor.
- **Confirmación:** mensaje al enviar con número de solicitud y aviso de tiempo de respuesta (24 h, como hoy).
- **Acuse al solicitante:** correo automático de recepción.

## Mapeo Forms → CRM
Al enviar, crear un registro en `Solicitudes` con `Estado = "Solicitud"` y copiar cada campo según la última columna de la tabla. Los adjuntos de cotización se asocian creando registros en `Cotizaciones` (o quedan en la solicitud para que el operador los registre).

## Verificación
- [ ] No deja enviar sin los campos obligatorios.
- [ ] Un envío de prueba crea la solicitud en CRM con todos los datos y estado inicial correcto.
- [ ] El campo 10 se exige cuando hay proveedor sugerido.
