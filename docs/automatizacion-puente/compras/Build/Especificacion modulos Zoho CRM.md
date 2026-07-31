# Especificación de módulos personalizados — Zoho CRM

**Fecha:** 2026-06-18 · Para el implementador. Crear en `Setup → Customization → Modules and Fields`.
Tipos de campo Zoho usados: Single Line, Multi Line, Pick List, Number, Currency, Email, URL, Date, Checkbox, Lookup, User (Lookup a usuarios).

---

## Módulo `Proveedores`
Maestro de proveedores en la capa de orquestación. Campo único: RUT.
**Actualizado 2026-07-02** para reflejar el checklist v2.0 (Fase 0) y la Ficha_Proveedor v2 (Excel) — agrega representantes legales, dirección, tipo de DTE y verificación cruzada SII.

| Campo | Tipo | Notas |
|---|---|---|
| Razón social | Single Line | Obligatorio |
| RUT | Single Line | **Único.** Sin puntos, con DV |
| Nombre de fantasía | Single Line | |
| Giro | Single Line | |
| Correo | Email | |
| Dirección, Comuna, Ciudad, Región, País | Single Line / Pick List | |
| Teléfono | Phone | |
| Representante Legal 1 — Nombre, RUT, Correo, Teléfono | Single Line / Email / Phone | Subformulario o 4 campos prefijados |
| Representante Legal 2 — Nombre, RUT, Correo, Teléfono | Single Line / Email / Phone | Igual que Representante 1; opcional |
| Tipo DTE | Pick List | Factura Electrónica / Factura Exenta / Boleta Electrónica / Boleta de Honorarios / otros |
| Banco | Pick List | Lista de bancos |
| Tipo de cuenta | Pick List | Corriente / Vista / Ahorro |
| N° cuenta | Single Line | Crítico para TXT |
| Email pago | Email | |
| Forma de pago | Pick List | Caja chica / Crédito en nómina |
| Plazo de pago (días) | Number | |
| Razón Social SII, Giro SII, Dirección SII, Documentos DTE Autorizados SII | Single Line / Multi Line | Se completan tras consultar el SII (manual, Fase 1) |
| Coincide Razón Social / Giro / Dirección / DTE | Pick List (fórmula) | Sí / No / Pendiente, comparando contra lo ingresado |
| Situación SII | Pick List | Vigente / No vigente / Pendiente |
| Estado proveedor | Pick List | En validación / Apto / Rechazado |

Regla: `Estado proveedor = Apto` solo si `Situación SII = Vigente`, Banco + Tipo de cuenta + N° cuenta + Email pago están completos, **y** las 4 verificaciones (Razón Social, Giro, Dirección, DTE) = Sí (ver checklist Fase 0 v2.0).

---

## Módulo `Solicitudes`
Origen del proceso (lo crea el formulario Zoho Forms).

| Campo | Tipo | Notas |
|---|---|---|
| Solicitante | User / Single Line | |
| Descripción | Multi Line | Obligatorio |
| Cantidad | Number | |
| Fecha requerida | Date | |
| Presupuesto estimado | Currency | |
| Centro de costo | Pick List | Resuelve el "dueño de presupuesto" |
| Cuenta contable | Pick List | |
| Proveedor sugerido | Lookup → `Proveedores` | |
| Motivo de selección | Multi Line | |
| Estado | Pick List | Los 10 estados del flujo (ver Blueprint) |

---

## Módulo `Cotizaciones`

| Campo | Tipo | Notas |
|---|---|---|
| Solicitud | Lookup → `Solicitudes` | Obligatorio |
| Proveedor | Lookup → `Proveedores` | |
| Monto cotizado | Currency | |
| Plazo de entrega | Single Line | |
| Adjunto | File Upload | Cotización |
| Seleccionada | Checkbox | Solo una por solicitud |

---

## Módulo `Ordenes_Compra`
Registro/espejo de la OC. No duplica el dato contable de Manager+: guarda N° y estado.

| Campo | Tipo | Notas |
|---|---|---|
| Solicitud | Lookup → `Solicitudes` | |
| Proveedor | Lookup → `Proveedores` | |
| N° OC Manager | Single Line | Se completa al emitir en Manager+ |
| Monto bruto c/IVA | Currency | **Base del tramo de aprobación** |
| Centro de costo | Pick List | |
| Cuenta contable | Pick List | |
| Link expediente SharePoint | URL | Carpeta del expediente |
| Aprobador asignado 1 | User | Lo setea `resolverAprobador`. Siempre se completa |
| Resultado aprobación 1 | Pick List | Pendiente / Aprobada / Rechazada |
| Aprobador asignado 2 | User | Lo setea `resolverAprobador`. **Solo** en tramo >$5.000.000 (doble firma) |
| Resultado aprobación 2 | Pick List | Pendiente / Aprobada / Rechazada / No aplica — "No aplica" si el tramo no exige doble firma |
| Recepción conforme | Checkbox | Bloquea avance a "En pago" |
| Fecha recepción | Date | |
| Responsable recepción | User | |
| N° Factura | Single Line | Se completa al recibir la factura del proveedor (vía Acepta en Manager+) |
| Fecha factura | Date | |
| Fecha pago | Date | Se completa al confirmar el abono bancario |
| Motivo rechazo | Multi Line | Obligatorio si `Estado = Rechazada` |
| Excede presupuesto | Checkbox | Lo setea `validarPresupuesto`. Informativo — **no bloquea** el flujo, solo alerta |
| Fecha entrada aprobación | DateTime | Lo setea `resolverAprobador`. Base de los recordatorios de aprobación pendiente |
| Fecha entrada facturada | DateTime | Se setea con un Workflow Rule (sin código) cuando `Estado` pasa a "Facturada". Base del recordatorio de recepción conforme |
| Estado | Pick List | Los 10 estados del flujo + `Rechazada` (ver `Blueprint - Proceso Compras y Proveedores.md`) |

---

## Módulo `Presupuestos`
Tabla paramétrica ligera para la alerta de presupuesto (Task 2.5 del plan). **No reemplaza** un módulo de presupuesto real de Odoo — es solo el techo de gasto por centro de costo y mes, mantenido a mano por Finanzas.

| Campo | Tipo | Notas |
|---|---|---|
| Centro de costo | Pick List | Mismo picklist que en `Solicitudes`/`Ordenes_Compra` |
| Período | Single Line | Formato `AAAA-MM`, ej. `2026-07` |
| Monto asignado | Currency | Techo de gasto para ese centro + período |
| Activo | Checkbox | Permite desactivar una fila sin borrarla |

Regla: `Comprometido` de un centro+período = suma de `Monto_bruto_c_IVA` de todas las `Ordenes_Compra` de ese centro y período con `Estado` distinto de `Rechazada`. Si `Comprometido > Monto_asignado`, la función `validarPresupuesto` marca `Excede_presupuesto = true` en la OC más reciente y notifica (ver `Workflow Rules - Alertas y Recordatorios.md`).

---

## Módulo `Parametros_Aprobacion`
Tabla paramétrica de la matriz de aprobaciones. Editable sin tocar el Blueprint.

| Campo | Tipo | Notas |
|---|---|---|
| Monto desde | Currency | Inclusive |
| Monto hasta | Currency | Inclusive (vacío = sin tope) |
| Aprobador 1 | User | |
| Aprobador 2 | User | Solo doble firma; opcional |
| Activo | Checkbox | |

**Filas iniciales (CLP bruto c/IVA):**
| Desde | Hasta | Aprobador 1 | Aprobador 2 |
|---|---|---|---|
| 0 | 500.000 | Dueño del presupuesto* | — |
| 500.001 | 1.000.000 | Cecilia Ramírez | — |
| 1.000.001 | 5.000.000 | Patricio Fernández | — |
| 5.000.001 | (vacío) | Patricio Fernández | Constanza Daniels |

\* "Dueño del presupuesto" se resuelve por centro de costo en `resolverAprobador` (ver borradores Deluge).

---

## Estados del Blueprint (los 10)
`Solicitud → Cotización → En aprobación → Aprobada → Proveedor validado → OC emitida → Facturada → Recepción conforme → En pago → Pagada`

Especificación completa (criterios de transición, campos obligatorios por etapa, quién ejecuta cada paso y qué función Deluge dispara) en `Build/Blueprint - Proceso Compras y Proveedores.md`.
