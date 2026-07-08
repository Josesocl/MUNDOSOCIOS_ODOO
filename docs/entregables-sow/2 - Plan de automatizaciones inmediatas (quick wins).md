# Entregable 2 — Plan de automatizaciones inmediatas (quick wins)

**Cliente:** MundoSocios — CChC · **Consultor:** JR Jottar (IBS) · **Fecha:** 2026-06-23
**Criterio:** automatizaciones *simples*, en herramientas ya implementadas (Zoho Forms, Excel/macros, plantillas, flujos básicos), que generen alivio visible **antes** de Odoo y dejen **activos reutilizables** en la migración. No incluye desarrollo de sistemas.

---

## 1. Priorización (impacto vs. esfuerzo)

| # | Quick win | Dolor que ataca (Entregable 1) | Impacto | Esfuerzo | Herramienta |
|---|---|---|---|---|---|
| QW1 | **Checklist de campos críticos del proveedor** | #1 TXT frágil | Alto | Bajo | Plantilla + ficha proveedor |
| QW2 | **Plantilla de control de nómina con validaciones** (detecta NC/anticipos negativos, caracteres especiales, descripción >400, campos vacíos) | #1 TXT frágil | Alto | Medio | Excel/Sheets + reglas |
| QW3 | **Cálculo automático de UF del día** para cuota social | #5 UF manual | Medio | Bajo | Excel/Sheets (web del SII / fórmula) |
| QW4 | **Formulario Zoho de solicitud con campos obligatorios** | #7 trazabilidad, retrabajo | Medio-alto | Bajo | Zoho Forms |
| QW5 | **Plantilla única de Orden de Compra** | #3 doble registro | Medio | Bajo | Word/Excel |
| QW6 | **Estructura estándar de carpetas SharePoint + nomenclatura** | respaldo/trazabilidad | Medio | Bajo | SharePoint |
| QW7 | **Limpieza asistida del archivo de preconciliación** (macro que normaliza columnas y quita caracteres) | #2 conciliación | Medio | Medio | Excel macro |
| QW8 | **Matriz de aprobaciones documentada + plantilla de visado** | #9 aprobaciones informales | Medio | Bajo | Documento + plantilla |

## 2. Detalle de cada quick win

### QW1 — Ficha de proveedores con verificación SII
Elaborado y construido (`Fase 0/Checklist campos criticos del proveedor.md` v2.0 + `Herramientas Operativas/01_Ficha_Proveedor_MundoSocios.xlsx`). Reúne datos de empresa, representantes legales, tipo de documento tributario y datos bancarios, y cruza Razón Social/Giro/Dirección/DTE contra el SII. Regla: un proveedor no avanza a "apto" sin SII vigente, datos bancarios completos y las 4 verificaciones SII coincidentes. **Evita la causa raíz #1 de errores de TXT.**

### QW2 — Plantilla de control de nómina con validaciones
Construido (`Herramientas Operativas/03_Control_Nomina_Pago_MundoSocios.xlsx`). Marca en rojo: documentos en negativo (NC/anticipos), descripciones con caracteres especiales o >400, y filas con datos faltantes. Antes de emitir, la planilla "avisa" lo que romperá el TXT.

### QW3 — Cálculo automático de UF del día
Reemplazar la consulta manual al SII por una celda que traiga la UF del día (servicio público de UF / fórmula) y calcule automáticamente Empresa = UF×1,44 y Persona = UF×0,48. Reduce error y tiempo en cada incorporación.

### QW4 — Formulario Zoho de solicitud con campos obligatorios
Ya especificado (`Fase 0/Formulario Zoho - Solicitud de Compra.md`). Impide solicitudes incompletas, principal causa de rechazo/retrabajo.

### QW5 — Plantilla única de Orden de Compra
Ya elaborada (`Fase 0/Plantilla Orden de Compra.md`). Estandariza el pedido que hoy va suelto por correo a Cecilia.

### QW6 — Estructura estándar de carpetas SharePoint
Ya definida (`Fase 0/Convencion de carpetas SharePoint.md`). Un expediente por OC, con link en el registro.

### QW7 — Limpieza y cuadratura automática de la conciliación
Construido (`Herramientas Operativas/05_Conciliacion_Bancaria_MundoSocios.xlsx`, sin macros — solo fórmulas). Se pega el export de preconciliación y la planilla arma sola la hoja en el formato exacto de "Conciliación Manager" (6 columnas, sin celdas extra), marca en rojo filas con RUT/N° documento faltante, y calcula automáticamente si Cargo y Abono cuadran contra los totales de la Cartola del banco (Depósitos, Otros Abonos, Cheques, Otros Cargos), mostrando la diferencia exacta si no cuadra.

### QW8 — Matriz de aprobaciones + plantilla de visado
Ya elaborada (`Fase 0/Politica de aprobaciones de compras.md`). Formaliza quién aprueba según monto, hoy resuelto informalmente por correo.

## 3. Estado de avance
Los 8 quick wins están construidos: QW1, QW4, QW5, QW6, QW8 como documentación/configuración lista para usar; QW2, QW3 y QW7 como planillas Excel operativas (sin macros, solo fórmulas) en `Herramientas Operativas/`, verificadas con recálculo real (0 errores de fórmula).

## 4. Activos que quedan para Odoo
Checklist de proveedor, matriz de aprobaciones, formulario estandarizado y nomenclatura documental se traducen directamente en configuración de Odoo (validaciones de proveedor, reglas de aprobación de compras, formularios y gestión documental).
