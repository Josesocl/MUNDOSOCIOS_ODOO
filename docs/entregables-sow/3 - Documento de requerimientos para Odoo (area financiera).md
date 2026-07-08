# Entregable 3 — Documento de requerimientos para Odoo (área financiero-contable)

**Cliente:** MundoSocios — CChC · **Consultor:** JR Jottar (IBS) · **Fecha:** 2026-06-23
**Propósito:** insumo directo para la Fase 0/1 del implementador Odoo. Traduce los dolores del diagnóstico (Entregable 1) en requerimientos funcionales, mapeados a módulos de **Odoo Enterprise**.

---

## 1. Módulos Odoo involucrados
Purchase, Accounting, Inventory (recepción), Expenses (rendiciones), Invoicing/Subscriptions (notas de cobro recurrentes), Sales/Website + Portal (socios), Studio (campos a medida y aprobaciones), Documents (respaldo).

## 2. Requerimientos por proceso

### 2.1 Compras y cuentas por pagar
- **RF-01** Requisición de compra con campos obligatorios (centro de costo, cuenta, presupuesto, motivo de selección) → *Purchase: Purchase Agreements / Requisitions*.
- **RF-02** Matriz de aprobación paramétrica por monto bruto c/IVA y centro de costo, con doble firma sobre umbral → *Purchase Approvals / Studio*.
- **RF-03** Control de presupuesto disponible **antes** de aprobar → *Accounting: Budgets / Analytic*.
- **RF-04** OC que consume saldo contra múltiples documentos tributarios → *Purchase ↔ Vendor Bills (matching 3 vías)*.

### 2.2 Proveedores
- **RF-05** Maestro único de proveedor con validación de campos críticos (datos bancarios) bloqueante, incluyendo dirección completa, representantes legales (hasta 2) y tipo de documento tributario (DTE) que emite.
- **RF-06** Validación de situación tributaria SII por RUT (vía API/conector) al crear/editar proveedor, incluyendo verificación cruzada de Razón Social, Giro, Dirección y Documentos DTE autorizados contra lo declarado por el proveedor (hoy manual, ver `Fase 0/Checklist campos criticos del proveedor.md` v2.0 y `01_Ficha_Proveedor_MundoSocios.xlsx`).
- **RF-06b** Los datos bancarios del proveedor deben quedar visibles/validados también en el proceso de pago (nómina), no solo al crear el proveedor — evita pagos a cuenta incorrecta y refuerza RF-05.

### 2.3 Recepción de facturas (DTE)
- **RF-07** Integración de recepción de DTE (hoy Acepta/Sovos) hacia *Vendor Bills*, con asociación automática a OC.

### 2.4 Pagos y nóminas
- **RF-08** Generación de archivo de pago (TXT) **integrado a Banco de Chile**, eliminando la edición manual del archivo.
- **RF-09** Manejo nativo de anticipos y notas de crédito en el pago (sin ajustes manuales que hoy rompen el TXT).
- **RF-10** Nóminas separadas (proveedores / reembolsos equipo) como diarios o procesos de pago distintos.
- **RF-11** Validaciones de datos que hoy rompen el TXT (caracteres, longitud, campos vacíos) embebidas en el modelo.

### 2.5 Rendiciones
- **RF-12** Gestión de gastos/reembolsos del equipo → *Expenses*, con flujo de aprobación y pago.

### 2.6 Conciliación bancaria
- **RF-13** Importación de cartola y **reglas de conciliación automática** que cubran más que el ~78% actual.
- **RF-14** Soporte a casos especiales: convenios **PAC** (un documento ↔ varios abonos) y viceversa.
- **RF-15** Trazabilidad OT/analítica en todos los movimientos (incluidos devengos) para evitar excepciones.

### 2.7 Recaudación / cuota social
- **RF-16** Generación masiva de **notas de cobro** mensuales (~1.500) con asiento automático → *Invoicing / Subscriptions*.
- **RF-17** Cálculo automático del valor en UF (Empresa 1,44 / Persona 0,48) según UF del día.
- **RF-18** Conciliación pago–socio–período, pagos parciales y morosidad.
- **RF-19** Integración con medios de pago recurrente (Webpay/Toku) y mailing de cobro.

### 2.8 Fondos propios vs. terceros
- **RF-20** Separación contable estricta de fondos propios y de terceros (seguros) → *diarios/analítica dedicados*, con reportes de fondos recaudados vs. pagos a aseguradoras.

### 2.9 Portal del socio
- **RF-21** Portal donde el socio vea estado de cuota, seguros contratados, historial de actividades y beneficios.

### 2.10 Boletas de honorarios y otros documentos
- **RF-22** Manejo de boletas de honorarios con **retención (13,75%)** y tipos de documento diferenciados (factura afecta/exenta, NC, ND, BOR, provisiones) → *Vendor Bills / impuestos de retención*.

### 2.11 Solicitudes internas como origen de compra
- **RF-23** Captura estructurada de solicitudes internas (sala, alimentación, pasajes, alojamiento) que hoy entran por formulario Zoho/correo y derivan en OC → *Purchase Requisitions + portal/formularios*, reemplazando las planillas Drive paralelas.

### 2.12 Devengos y carga masiva
- **RF-24** Generación de devengos (cuota social y seguros) como asientos automáticos/recurrentes, reemplazando la carga masiva por Excel hoy hecha vía el importador de Manager+.

## 3. Integraciones requeridas
| Integración | Hoy | Requerimiento Odoo |
|---|---|---|
| Recepción DTE (Acepta/Sovos) | Manual en Manager+ | Conector a Vendor Bills |
| Banco de Chile | TXT manual editado | Archivo de pago + conciliación integrados |
| SII | Web manual (UF, situación tributaria) | API situación tributaria + valor UF |
| Webpay / Toku | Manual | Conciliación de pagos recurrentes |
| Buk (RRHH) | — | Integración a evaluar |
| Migración de maestros | — | Proveedores, socios, plan de cuentas, centros de costo |

## 4. Datos a migrar (limpios)
Maestro de proveedores validado, plan de cuentas con niveles, centros de costo / líneas de negocio, socios y beneficiarios, histórico de cuota social y devengos.

## 5. Reglas de negocio a preservar
- Matriz de aprobaciones (ver Entregable 2 / política).
- Campos críticos del proveedor para pago.
- Separación fondos propios/terceros.
- Nóminas de pago programadas con fecha editable de abono.
- Conciliación mensual con manejo de PAC y devengos.

> Nota: el diseño detallado del "sistema puente" (Zoho CRM + Blueprint + Deluge + archivo a Manager+) sirve como **especificación de comportamiento esperado**; en Odoo, la mayoría de esos requerimientos se cubren con configuración nativa, no con desarrollo.

> **Nota del repositorio (2026-07-07):** RF-17 quedó desactualizado — los valores reales 2026 de cuota social son 1 UF persona / 3 UF empresa (+1 UF por miembro desde el 4º), con devengo anual; ver `docs/correcciones/Correcciones_pendientes_OneDrive.md` §10 y la especificación de suscripciones en `docs/odoo/`.
