# Correcciones pendientes en OneDrive — lista de ediciones exactas

El conector de esta sesión solo lee OneDrive; estas ediciones hay que aplicarlas a mano (o en una sesión de Claude en el Mac, que sí escribe en la carpeta). Ruta raíz: `.../CONSULTORÍA JR JOTTAR/CLIENTES CONSULTORA JRJ/MUNDOSOCIOS ODOO/`

## 1. Reemplazar el blueprint corrupto de proveedores 🔴

`FLUJOS DE PROCESO/BP_Proceso_Creación_Proveedor_MundoSocios.docx` tiene portada de "Creación de Proveedor" pero el cuerpo es el blueprint de Experiencia/Atención completo.
**Acción:** reemplazar su contenido con `docs/flujos-proceso/BP_Proceso_Creacion_Proveedor.md` de este repo (generar .docx desde el .md). No entregarlo a ningún partner antes de esto.

## 2. Banner "FUERA DE ALCANCE" faltante en 4 documentos de Build/ 🔴

Está en `00_INDICE` y en los 3 documentos raíz, pero falta en los documentos individuales. Pegar al inicio (tras el título) de:
- `Automatizacion Puente Compras/Build/Blueprint - Proceso Compras y Proveedores.md` (verificado: no lo tiene)
- `Automatizacion Puente Compras/Build/Borradores Deluge.md`
- `Automatizacion Puente Compras/Build/Especificacion modulos Zoho CRM.md`
- `Automatizacion Puente Compras/Build/Workflow Rules - Alertas y Recordatorios.md`

Texto a pegar:

```markdown
> ⚠️ **FUERA DE ALCANCE (decisión del cliente, 2026-07-06).** La capa Zoho CRM
> (módulos, Blueprint, Approval Process, Deluge) NO se implementará. Este
> documento queda como referencia histórica / insumo de requerimientos Odoo.
> El alcance vigente es Fase 0 + Herramientas Operativas. Ver
> `00_HANDOFF_Contexto_Proyecto_MundoSocios.md` §0.4.
```

## 3. `Build/00_INDICE - Guia de implementacion.md` desactualizado 🟡

- Donde dice **"37 tests"** → **"45 tests"**.
- Donde nombra **BaseAPI como proveedor** del Validador SII → **API Gateway (default; BaseAPI queda como `--proveedor baseapi`, legado, se discontinúa dic-2026)**.

## 4. Entregable 1 — `Entregables SOW/1 - Informe de diagnostico...` 🟡

- §5: donde dice que los quick wins atacan los dolores **"1, 5, 6 y 9"** → **"1, 2, 3, 5, 7 y 9"** (los que realmente mapea el Entregable 2; el #6 se cubre solo indirectamente vía QW1).
- §4, hallazgo #13 ("Importador subutilizado"): asignar impacto (propuesto: **Medio**) — hoy la celda está vacía ("—").
- Regenerar el .docx después de editar el .md.

## 5. Entregable 2 — `Entregables SOW/2 - Plan de automatizaciones...` 🟡

- Tabla QW7: donde dice **"macro que normaliza columnas"** → **"fórmulas que normalizan columnas (sin macros)"** (coherente con el detalle y §3).
- QW3: actualizar la redacción de propuesta futura ("Reemplazar la consulta manual...") a estado **construido** (`04_Calculo_UF_Cuota_Social_MundoSocios.xlsx`), coherente con §3.
- Agregar (opcional, recomendado): por cada QW una línea "responsable de adopción / fecha objetivo / métrica"; y una nota final "dolores #4, #8 y #12 se difieren a gestión del cambio y a Odoo".
- Regenerar el .docx.

## 6. Entregable 5 — `Entregables SOW/5 - Guia de entrevistas` 🟢

- B7: "Constanza" → **"Constanza Daniels (Gerente General)"**.
- Tabla de participantes: identificar por nombre al **"encargado de conciliación"** (preguntar a Patricio) o marcar explícitamente "nombre por confirmar".

## 7. `Fase 0/Politica de aprobaciones de compras.md` 🟡

- §5 aún referencia la tabla `Parametros_Aprobacion` de Zoho CRM (obsoleta tras el recorte): reemplazar por referencia a la matriz en `02_Registro_y_Plantilla_OC_MundoSocios.xlsx`.
- Sigue "borrador": gestionar el visto bueno escrito de Patricio (mejora #1 de la evaluación).

## 8. `Fase 0/Plantilla Orden de Compra.md` 🟢

Agregar al inicio: "Materializada en `Herramientas Operativas/02_Registro_y_Plantilla_OC_MundoSocios.xlsx` (vigente); este documento queda como especificación."

## 9. Higiene de archivos 🟢

- Eliminar `Validador SII (Python standalone)/__pycache__/` y `tests/__pycache__/`.
- Duplicación de proxy: dejar **una** copia (propuesto: `Validador SII (Python standalone)/proxy-apigateway/`) y en `Proxy SII (Squid Docker)/` un README de una línea apuntando a la vigente — o eliminarla.
- `FLUJOS DE PROCESO`: marcar cuál versión del manual de sala rige (`MANUAL SOLICITUD SALA...-JRJ.md` vs la normal) y archivar la otra; revisar duplicados `_ocr`/`_ocr_ocr`.
- Raíz del proyecto: mover `OneDrive_1_6-5-2026.zip` y `OneDrive_2_6-5-2026.zip` a una subcarpeta `ARCHIVO/` (ya están descomprimidos en FLUJOS DE PROCESO).

## 10. Entorno Claude del Mac 🟡

- `~/.claude/settings.json`: reemplazar por `docs/correcciones/settings.json.recomendado` (elimina `bypassPermissions` global y los permisos `rm`/`bash *`).
- `~/.claude/skills/.../daily-timebox/SKILL.md` (copia en `Claude/Scheduled/daily-timebox/`): reemplazar por `docs/correcciones/daily-timebox_SKILL_corregido.md` (frontmatter duplicado corregido y pasos ordenados).
- Instalar en el Mac la skill de contexto del proyecto: copiar `.claude/skills/mundosocios-context/` de este repo.
