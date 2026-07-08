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
- `herramientas/generador-devengos/` — generadores de devengos para Manager+ desde un maestro único: seguros mensuales (UF propia por seguro) y cuota social anual (reglas 2026: 1 UF persona / 3 UF empresa + adicionales). Formato verificado contra los archivos productivos JUL-26/ENE-26. 19 tests.
- `herramientas/cruzador-pagos/` — genera el borrador de PRECONCILIACIÓN desde la cartola Banco de Chile + resumen Transbank + maestro: clasifica movimientos, cuadra abonos Transbank y propone RUT para transferencias por match de nombre. 7 tests.
- `.claude/skills/mundosocios-context/` — contexto del proyecto para sesiones de Claude.

## Documentos migrados desde OneDrive

- `docs/handoff/` — `00_HANDOFF_Contexto_Proyecto_MundoSocios.md` (con notas de actualización 2026-07-07/08) y `Analisis_Ficha_Requerimientos_Odoo_Mexico_MundoSocios.md`.
- `docs/entregables-sow/` — los 5 entregables del SOW en `.md` (E1 diagnóstico, E2 quick wins, E3 requerimientos Odoo, E4 gestión del cambio, E5 guía de entrevistas), copia textual de OneDrive; las correcciones conocidas están anotadas en `docs/correcciones/`.

## Pendiente de migrar desde OneDrive

- `FLUJOS DE PROCESO/*.md` (manuales transcritos y flujos) y `Automatizacion Puente Compras/` (Fase 0, diseño de referencia y Build) — misma mecánica de copia textual.
- **Validador SII (código Python)**: el conector de OneDrive no permite leer archivos `.py`; migrarlo desde el Mac (copiar la carpeta al repo y hacer commit).
- La versión maestra de todo sigue en OneDrive; ante diferencias, manda OneDrive.
