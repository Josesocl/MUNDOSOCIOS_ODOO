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

## 10. Actualizaciones por precisiones del 2026-07-07 🔴

- **Valores de cuota social:** todos los documentos que digan "Empresa 1,44 UF / Persona 0,48 UF" están desactualizados (E1 §3.8, E2 QW3, E3 RF-17, BP Recaudación §1.1-1.2, handoff §7). Valor real 2026: **Persona 1 UF; Empresa 3 UF hasta 3 miembros + 1 UF por miembro desde el 4º**; devengo anual único al 1 de enero (verificado contra `DEVENGO CUOTA SOCIAL * ENE-26.xlsx`).
- **Cuentas cuota social persona:** el BP Recaudación §1.2 dice 1150001/3210002 para ambas; lo real es persona **1150002/3210001** (empresa sí 1150001/3210002).
- **UF por seguro:** complementario usa la UF del día 9; catastrófico la del último día del mes anterior (los documentos hablan de una sola "UF del día").
- **Javiera Valdovinos ya no está en MundoSocios:** quitarla de E1 (§3.13), E5 (tabla de participantes), BP Recaudación §1.4 y handoff §1. Nuevo actor: **Marcos Ibarra**, Analista de Administración y Control de Gestión (envía cierres diarios a Addval; apoyo a recaudación).
- **Addval:** ciclo real = envío diario L-V por Marcos + 48 h de plazo para subir (no "frecuencia errática" sin regla). Actualizar PC-02 del BP.
- **Zoho reabierto parcialmente** (reunión 2026-07-07 con Alexander Gutiérrez, soporte Zoho): Sandbox con datos productivos, módulo Proveedores activado, validación RUT por función personalizada, SII vía API Gateway. Actualizar el aviso "FUERA DE ALCANCE" de Build/ (el descarte total ya no es exacto: el diseño sirve de especificación para lo que construya Alexander).

## 11. Entorno Claude del Mac 🟡

- `~/.claude/settings.json`: reemplazar por `docs/correcciones/settings.json.recomendado` (elimina `bypassPermissions` global y los permisos `rm`/`bash *`).
- `~/.claude/skills/.../daily-timebox/SKILL.md` (copia en `Claude/Scheduled/daily-timebox/`): reemplazar por `docs/correcciones/daily-timebox_SKILL_corregido.md` (frontmatter duplicado corregido y pasos ordenados).
- Instalar en el Mac la skill de contexto del proyecto: copiar `.claude/skills/mundosocios-context/` de este repo.
