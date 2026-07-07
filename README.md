# MUNDOSOCIOS_ODOO

Repositorio del proyecto **MundoSocios (CChC) — diagnóstico financiero-contable, automatización puente y migración a Odoo** (consultoría IB Solución / JR Jottar).

Los materiales de trabajo del proyecto viven hoy en OneDrive:
`Documentos OneD IBS/CONSULTORÍA JR JOTTAR/CLIENTES CONSULTORA JRJ/MUNDOSOCIOS ODOO/`
(punto de entrada: `00_HANDOFF_Contexto_Proyecto_MundoSocios.md`).

## Contenido actual

- `EVALUACION_PROYECTO_2026-07-07.md` — evaluación completa del proyecto: estado de los entregables SOW, herramientas operativas, Validador SII, flujos de proceso, preparación para Odoo y entorno de trabajo, con un plan de mejoras priorizado (16 acciones).

## Propuesta de estructura (mejora #13 de la evaluación)

Migrar a este repositorio todo lo textual y el código, dejando OneDrive para binarios de intercambio con el cliente:

```
docs/
  handoff/            # 00_HANDOFF y actas
  entregables-sow/    # E1–E5 en .md
  flujos-proceso/     # blueprints y manuales transcritos
  fase-0/             # política, checklist, convenciones
herramientas/
  validador-sii/      # código Python + tests
  proxy-apigateway/   # Squid/Docker (una sola copia)
.claude/
  skills/mundosocios-context/SKILL.md   # contexto del proyecto para sesiones de Claude
```
