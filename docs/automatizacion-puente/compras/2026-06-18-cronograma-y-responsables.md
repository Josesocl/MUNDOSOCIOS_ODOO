# Cronograma y responsables — Automatización Compras y Proveedores

> **⚠️ FUERA DE ALCANCE (decisión del cliente, 2026-07-06):** este cronograma es 100% del proyecto Zoho CRM (Fases 1-2), que MundoSocios decidió no construir. Sin ese proyecto, no hay roles de "Consultor" configurando Zoho ni hitos de accesos/licencias que gestionar. Queda como referencia histórica. El alcance vigente (Fase 0 + Herramientas Operativas) no requiere cronograma de implementación — son herramientas ya entregadas y usables hoy.

**Fecha:** 2026-06-23 · Arranque: hoy (no se espera al 01-jul). Cierre pre-Odoo: oct-2026. Migración Odoo: ~nov-2026.

## Roles
- **Consultor (IBS / JR Jottar):** diseño, especificaciones, configuración Zoho CRM/Forms, funciones Deluge, acompañamiento.
- **Patricio Fernández (Adm. y Finanzas):** owner funcional; valida políticas; cuenta productiva de SharePoint; layout de Manager+; decisión API SII.
- **Cecilia Ramírez:** proceso operativo de OC; pruebas de usuario.
- **TI MundoSocios:** accesos, licencias Zoho CRM, cuentas/buzones.
- **Aprobadores:** dueños de presupuesto, Cecilia, Patricio, Constanza Daniels — pruebas de aprobación.

## Cronograma

| Fase | Ventana | Tareas (ref. plan) | Responsable principal | Apoyo |
|---|---|---|---|---|
| **0 — Estandarizar** | 23-jun → 04-jul | 0.0 accesos | TI MundoSocios | Patricio |
| | | 0.1 política aprobaciones, 0.2 checklist proveedor, 0.4 carpetas/plantilla OC, 0.3 formulario | Consultor | Patricio / Cecilia |
| **1 — Proceso y aprobaciones** | 07-jul → 22-ago | 1.1–1.5 módulos + Forms | Consultor | — |
| | | 1.6–1.7 matriz y ruteo aprobación | Consultor | Patricio |
| | | 1.8 Blueprint, 1.9 recepción conforme, 1.10 dashboards | Consultor | Cecilia |
| | | Pruebas de usuario Fase 1 | Cecilia + aprobadores | Consultor |
| **2 — Integraciones** | 25-ago → 26-sep | 2.0 layout Manager+ | Patricio | Consultor |
| | | 2.1 SII (decisión API + función) | Consultor | Patricio |
| | | 2.2–2.4 exportadores y reflejo de estado | Consultor | Patricio |
| | | 2.5 alertas presupuesto / recordatorios | Consultor | — |
| **Cierre pre-Odoo** | oct | C.1 depurar maestro, C.2 doc traspaso | Consultor | Patricio |

## Hitos de decisión (bloqueantes si se atrasan)
1. **Accesos y cuentas** (Task 0.0) — antes de iniciar Fase 1. Responsable: TI / Patricio.
2. **Validación de la política de aprobaciones** (Task 0.1) — antes de Task 1.7. Responsable: Patricio.
3. **Layout de carga de Manager+** (Task 2.0) — antes de Tasks 2.2–2.4. Responsable: Patricio.
4. **Proveedor de API SII** (Task 2.1) — antes de automatizar validación. Responsable: Patricio.

## Dependencias críticas
- Fases 0 y 1 **no** dependen de Manager+ → se puede avanzar sin esperar el layout.
- La validación SII automática (Fase 2) depende de elegir y contratar la API de terceros; mientras tanto opera manual-asistida.

## Insumos pendientes del cliente (para el consultor)
- Centros de costo y su "dueño de presupuesto".
- Usuarios Zoho de cada aprobador.
- Listas para picklists: bancos, cuentas contables, centros de costo.
