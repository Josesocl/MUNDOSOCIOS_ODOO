# MUNDOSOCIOS_ODOO

Repositorio del proyecto **MundoSocios (CChC) — diagnóstico financiero-contable, automatización puente y migración a Odoo** (consultoría IB Solución / JR Jottar).

Los materiales de trabajo del proyecto viven hoy en OneDrive:
`Documentos OneD IBS/CONSULTORÍA JR JOTTAR/CLIENTES CONSULTORA JRJ/MUNDOSOCIOS ODOO/`
(punto de entrada: `00_HANDOFF_Contexto_Proyecto_MundoSocios.md`).

## Contenido

- `EVALUACION_PROYECTO_2026-07-07.md` — evaluación completa del proyecto: estado de los entregables SOW, herramientas operativas, Validador SII, flujos de proceso, preparación para Odoo y entorno de trabajo, con un plan de mejoras priorizado (16 acciones).
- `docs/odoo/Especificacion_Suscripciones_Cobro_Recurrente_Odoo.md` — configuración de los productos recurrentes (cuota social anual, seguros con cobro mensual) para el partner Odoo.
- `docs/automatizacion-puente/Plan_Automatizacion_Cobro_Recurrente_Puente.md` — plan jul→nov 2026 para automatizar el ciclo devengo→cobro→registro→conciliación con las herramientas actuales (Zoho estándar, Manager+ por archivo, Excel/Python), en 4 olas.
- `docs/fase-0/Politica_morosidad_y_pagos_parciales_BORRADOR.md` — cierra DP-04/DP-06 y PC-08 del BP de Recaudación (requiere validación GG/Recaudación).
- `docs/flujos-proceso/BP_Proceso_Creacion_Proveedor.md` — reemplazo del blueprint .docx corrupto.
- `docs/correcciones/Correcciones_pendientes_OneDrive.md` — ediciones exactas a aplicar en los archivos de OneDrive (banners, inconsistencias E1/E2/E5, higiene) + `settings.json` recomendado y skill daily-timebox corregida.
- `herramientas/generador-devengos/` — generador de los archivos mensuales de devengo de seguros para Manager+ desde un maestro único, con validación previa de RUTs y clientes (14 tests).
- `.claude/skills/mundosocios-context/` — contexto del proyecto para sesiones de Claude.

## Pendiente de migrar desde OneDrive

Entregables SOW y manuales en `.md`, Validador SII (código + tests) y proxy — ver mejora #13 de la evaluación. OneDrive queda para binarios de intercambio con el cliente (.docx/.xlsx/.pptx).
