# Evaluación completa del proyecto MundoSocios (CChC) — Odoo

**Fecha:** 2026-07-07 · **Consultor:** JR Jottar (IB Solución)
**Fuente evaluada:** carpeta OneDrive `Documentos OneD IBS/CONSULTORÍA JR JOTTAR/CLIENTES CONSULTORA JRJ/MUNDOSOCIOS ODOO` (estado al 2026-07-06) + configuración de trabajo con Claude.
**Alcance de esta evaluación:** estado general del proyecto, calidad y coherencia de los entregables, flujos de trabajo del negocio documentados, herramientas construidas, preparación para la migración a Odoo, y el entorno/las habilidades de trabajo (Claude, versionado, higiene documental), con mejoras accionables por bloque.

---

## 1. Resumen ejecutivo

El proyecto está en **buen estado de forma y contenido, pero con un déficit transversal de validación formal del cliente y varios cabos sueltos que conviene cerrar antes del blueprint definitivo de Odoo**.

| Bloque | Estado | Juicio breve |
|---|---|---|
| Entregables SOW (E1–E5) | 🟡 Bueno, en borrador | Paquete muy trazable y coherente; E1 y E4 siguen "borrador" a la espera de entrevistas; inconsistencias menores de redacción; requerimientos sin priorizar. |
| Fase 0 + Herramientas Excel | 🟡 Construido, no validado | Las 5 planillas existen y están verificadas con recálculo real; la Política de Aprobaciones y el checklist siguen sin visto bueno escrito de Patricio. Riesgo operativo #1: espejo manual de datos 01→03. |
| Validador SII + proxy | 🟢 Maduro, bloqueado por el cliente | 45/45 tests, proxy desplegado en GCP; solo falta contratar el token de API Gateway (~$10.000 CLP/mes) y verificar los campos JSON reales. |
| Flujos de proceso (AS-IS) | 🟡 Sólidos con vacíos | 15+ documentos leídos; manuales operativos honestos y útiles. Faltan 4 procesos clave y hay 1 blueprint corrupto (duplicado). |
| Preparación Odoo (propuestas) | 🔴 Decisiones abiertas | Las restricciones R1 (TXT), R2 (Webpay/PAC-PAT) y hosting (.sh vs Online) no están resueltas en la propuesta de Indasoge (563 UF). No firmar sin las respuestas de §6. |
| Entorno de trabajo / habilidades | 🔴 Mejorable | Repo GitHub vacío (todo vive solo en OneDrive), `bypassPermissions` global en Claude, skill con frontmatter duplicado, `__pycache__` y duplicaciones en OneDrive. |

**Las 5 acciones de mayor retorno inmediato** (detalle en §7):
1. Obtener el visto bueno escrito de Patricio a la Política de Aprobaciones y al checklist de proveedor (desbloquea todo el bloque vigente).
2. Contratar API Gateway y hacer la primera llamada real del Validador SII (todo lo demás ya está listo).
3. Corregir el `BP_Proceso_Creación_Proveedor.docx` corrupto y escribir el procedimiento de pago a aseguradoras / fondos de terceros (riesgo contable crítico sin procedimiento escrito).
4. Enviar a Indasoge las preguntas de hosting/TXT/pasarela antes de firmar (§6.3).
5. Versionar el proyecto en este repositorio Git (documentos .md + Validador SII) para dejar de depender de OneDrive como única fuente.

---

## 2. Entregables SOW (E1–E5)

### 2.1 Estado por entregable

| Entregable | Estado declarado | Evaluación |
|---|---|---|
| E1 Diagnóstico (13 subprocesos, 13 puntos críticos) | Borrador | Muy concreto y verificable (cuentas contables exactas, volúmenes, responsables). Pendientes declarados: caja chica, ajustes CxP, morosidad, volúmenes/tiempos, RACI. |
| E2 Quick wins (8 QW construidos) | Construido, 0 errores de fórmula | Trazable a los dolores del E1. Falta plan de despliegue (responsable, fecha, métrica por QW) — "construido" no es "en uso". |
| E3 Requerimientos Odoo (25 RF, 6 integraciones) | Completo | Cobertura casi total de los dolores. **Sin priorización MoSCoW ni criterios de aceptación**; supuestos sin decisión (Enterprise, Toku, Buk). |
| E4 Gestión del cambio | Borrador | El más incompleto: tabla de disposición 100% "por confirmar"; sin mapa de stakeholders ni plan B de key user. |
| E5 Guía de entrevistas | Completo | Bien alineada con los pendientes de E1 y E4. Falta agenda, plantilla de acta y aclarar 2 personas sin identificar. |

### 2.2 Inconsistencias detectadas (corregir en la próxima edición)

1. **E1 §5 vs E2:** E1 dice que los quick wins atacan los dolores "1, 5, 6 y 9"; la tabla de E2 mapea a 1, 2, 3, 5, 7 y 9. Los textos no cuadran.
2. **E2 QW7:** la tabla dice "macro que normaliza columnas"; el detalle y §3 dicen "sin macros — solo fórmulas".
3. **E2 QW3:** redactado como propuesta futura en §2 pero declarado "construido" en §3.
4. **E1 hallazgo #13:** sin impacto asignado en la tabla (celda "—").
5. **E5:** menciona a "Constanza" en B7 sin rol definido (es Constanza Daniels, GG — explicitarlo) y el "encargado de conciliación" queda sin nombre.
6. **E3:** introduce Toku, Buk y Odoo Enterprise sin decisión documentada del cliente.

Las cifras de fondo (UF 1,44/0,48, retención 13,75%, ~1.500 notas/mes, ~233 mov./cartola, 78/22% conciliación) **son consistentes en todos los documentos** — no hay contradicciones de fondo.

### 2.3 Mejoras al paquete SOW

- Añadir a E3 columna de **prioridad (MoSCoW) + dependencia de go-live**, y 1–2 criterios de aceptación medibles por RF (p. ej. RF-13: conciliación automática ≥ 90%).
- Marcar cada RF como **nativo / configuración / desarrollo** contrastando con `l10n_cl` y la ficha de Odoo México (§6).
- Añadir a E2 por cada QW: responsable de adopción, fecha objetivo y métrica ("errores de TXT por nómina: de X a 0"), más una sección "dolores no cubiertos y por qué" (#4, #8, #12).
- Completar E4 tras las entrevistas: mapa de disposición por persona, mini-mapa de stakeholders (incl. GG), KPIs de cambio y plan B de key user.
- E5: agendar las sesiones (cruzadas con las 3 sesiones de E4) y crear plantilla de acta estandarizada.

---

## 3. Fase 0, Herramientas Operativas y Validador SII

### 3.1 Fase 0 — el gap es la validación, no el contenido

| Documento | Estado |
|---|---|
| Checklist campos críticos proveedor | v2.0, el más maduro; falta confirmación contra un caso real de TXT. |
| Política de aprobaciones | **Borrador sin validar por Patricio**; §5 aún referencia la tabla Zoho obsoleta. |
| Convención carpetas SharePoint | Vigente; los 3 checks de validación (expediente de prueba, permisos) sin marcar. |
| Formulario solicitud de compra | Fuera de alcance parcial (correcto); la tabla de campos se conserva como checklist. |
| Plantilla OC | Especificación absorbida por `02_Registro_y_Plantilla_OC.xlsx` pero el .md no lo referencia. |

### 3.2 Flujo operativo 01→02→03→05 (+04) — riesgos

1. **Espejo manual de datos (riesgo #1):** la hoja `Proveedores` de la planilla 03 es copia de la 01; si se desactualiza, la alerta de cruce compara contra datos viejos y da **falsa seguridad**. No hay procedimiento ni fecha visible de "espejo actualizado al ___".
2. **Re-digitación:** el proveedor se tipea en 01, 02 y 03; el cruce detecta discrepancias pero no dice qué lado es el correcto.
3. **Aprobación por tramo sin motor:** al caer Zoho, el tramo se marca a mano en la OC; nada impide emitir sin la firma correcta ni detecta fraccionamiento de compras (regla explícita de la política).
4. **Trazabilidad por disciplina:** la llave expediente ↔ OC ↔ nómina ↔ conciliación depende del renombrado manual `SIN-OC_{Id}` → N° OC.
5. **Coedición:** 5 xlsx compartidos sin protección de hojas → fórmulas rotas y copias divergentes.

**Mejoras:** fuente única de proveedores (conexión/Power Query o procedimiento de refresco con fecha visible + listas desplegables en vez de tipeo libre); en la 02, columna calculada de tramo + campos obligatorios "Aprobado por / fecha / link a evidencia"; en la 03, alerta si una línea referencia OC sin aprobación registrada; control anti-fraccionamiento (suma de OC por proveedor+mes vs tramo); proteger hojas y celdas de fórmula.

### 3.3 Validador SII — listo salvo el token

Madurez alta: solo stdlib, CLI + servidor local + modo mock, **45/45 tests** (DV verificado contra implementación independiente con 5.000 RUTs), proxy Squid **ya desplegado y verificado en GCP** (capa gratuita). Migrado de BaseAPI (se discontinúa dic-2026) a API Gateway con costo confirmado (~$10.000 CLP/mes + ~$5/consulta).

**Único bloqueante:** no hay token real → los nombres de los campos JSON de respuesta siguen sin verificar. Pendiente de decisión de Patricio. Limitación conocida: el endpoint no trae Dirección ni DTE autorizados → 2 de las 4 verificaciones cruzadas siguen manuales.

**Inconsistencias a corregir:** `Build/00_INDICE` dice "37 tests" y BaseAPI (real: 45 y API Gateway). **Higiene:** eliminar `__pycache__/` de OneDrive; resolver la duplicación `Proxy SII (Squid Docker)/` vs `Validador SII/proxy-apigateway/` (dejar uno + puntero).

### 3.4 Aviso "FUERA DE ALCANCE" incompleto en Build/

El banner del recorte Zoho (2026-07-06) está en el índice y en los 3 documentos raíz, pero **`Blueprint - Proceso Compras y Proveedores.md` no lo tiene** (empieza directo con instrucciones de implementación) y los otros 3 de Build/ no fueron verificados. Quien abra un documento suelto podría empezar a implementar Zoho sin enterarse del recorte. Añadir el banner a los 4 restantes.

---

## 4. Flujos de trabajo del negocio (AS-IS)

### 4.1 Los tres cuellos de botella más costosos

1. **Ciclo TXT bancario editado a mano:** la fecha de pago se edita en Bloc de notas; campos vacíos del maestro, caracteres especiales, descripciones >400 y negativos rompen la carga; dos TXT por fecha (proveedores y personal). Es el punto de mayor riesgo de error en pagos.
2. **Devengo/recaudación/conciliación repartidos en 4 lugares:** Manager+, Zoho, Drive y Addval (~40 hrs/mes solo en recaudación; ~10 hrs/semana cruzando 3 fuentes; Addval sin SLA; separación de fondos propios/terceros sostenida a mano — riesgo crítico de auditoría).
3. **Incorporaciones, atención y experiencias sin sistema:** formulario WordPress no integrado y sin validación de RUT CChC; reembolsos en bandejas de correo personales sin ticket ni estado; inscripciones a experiencias re-digitadas y pagos verificados a mano contra cartolas.

### 4.2 Documentación: fortalezas y vacíos

**Sólido:** manuales operativos "hechos por quien opera" (nóminas, facturas/boletas, conciliación, devengos, proveedores/clientes, rendiciones) y 3 blueprints AS-IS/TO-BE (Recaudación —el más completo—, Compras, Experiencia) + plan de implementación de 5 fases.

**Problemas y vacíos a cerrar antes del blueprint definitivo:**
- **`BP_Proceso_Creación_Proveedor_MundoSocios.docx` está corrupto:** la portada dice "Creación de Proveedor" pero el cuerpo es el blueprint de Experiencia completo. Corregir antes de entregarlo a cualquier partner.
- **Sin procedimiento escrito:** pago a aseguradoras / rendición de fondos de terceros (facturas Vida Cámara de $22–48 M aparecen en nóminas sin ciclo documentado — riesgo PC-04 "crítico"), caja chica, morosidad/suspensión/pagos parciales, cierre contable mensual, nota de cobro mensual (plantillas y calendario).
- **Referencias rotas:** el manual de nóminas cita un "manual de ajuste cuentas por pagar" y el de conciliación un "Manual de ingresos" que no están en la carpeta.
- **Higiene de versiones:** duplicados .docx+.md y PDF+_ocr+_ocr_ocr; dos versiones del manual de sala (normal y "-JRJ") sin indicar cuál rige.

### 4.3 Quick wins adicionales sobre el stack actual (no requieren Odoo)

- **Cartola en Excel/CSV** del Banco de Chile en vez de PDF (elimina la transcripción y el archivo puente PRECONCILIACIÓN).
- **Script/validación para el TXT:** fijar fecha de pago sin Bloc de notas y validar longitudes/caracteres antes de la carga.
- **Zoho Desk** (ya incluido en Zoho One) para tickets de atención/reembolsos con número y estado — el quick win de mayor impacto en experiencia del socio.
- **Maestro único de pólizas:** consolidar los 4 "mantenedores" de seguros en un maestro que *genere* el archivo de 22 columnas (evita copiar el mes anterior) + validador previo de RUTs contra Manager+ (evita el ciclo "Cliente no existe → crear → reimportar").
- **SLA escrito con Addval** (viernes 12:00 ya propuesto) y una sola planilla de cruce alimentada por exportes.
- **UF automática en la plantilla de correo de incorporación** (merge field) — elimina la consulta manual diaria.

---

## 5. Preparación para Odoo — decisiones que bloquean

De la ficha de requerimientos de Odoo México (la mejor "verdad técnica" disponible) y su cruce con la propuesta de Indasoge (563 UF):

| Riesgo | Detalle | Estado |
|---|---|---|
| **R1 TXT bancario** | Odoo NO lo genera nativo; requiere desarrollo y **Odoo.sh** (no Online). Indasoge no lo separa como línea. | 🔴 Sin respuesta |
| **R2 Webpay/PAC/PAT** | No nativo; vía Nuvei/Toku u otro. 80% de la recaudación de seguros es PAC/PAT. ¿Las 40 hrs de Indasoge alcanzan? | 🔴 Sin respuesta |
| **R3 Buk** | Sin integración nativa; solo asiento manual con layout. Decidir: mantener Buk o migrar RRHH. | 🟡 Sin dueño ni plazo |
| **R4 UF en pantalla** | Suscripciones en UF se muestran en CLP al socio. ¿Aceptable para el portal? | 🟡 Por validar |
| Hosting | Odoo.sh vs Online condiciona R1. | 🔴 No especificado por Indasoge |

**Recomendación:** enviar a Indasoge las 5 preguntas ya redactadas en `Analisis_Ficha_Requerimientos_Odoo_Mexico_MundoSocios.md` §4 **antes de firmar**, y usarlas como criterio homogéneo con Addval y Odoo México. Otras decisiones de discovery que bloquean diseño: rol de Addval post-migración, política de morosidad, corte de saldos Manager+, portal 100% Odoo vs híbrido WordPress, caja chica.

---

## 6. Entorno de trabajo y habilidades (Claude, versionado, higiene)

### 6.1 Hallazgos

1. **Repositorio GitHub vacío:** `Josesocl/MUNDOSOCIOS_ODOO` no tiene ni una rama. Todo el proyecto (documentos, planillas, código Python) vive únicamente en OneDrive: sin historial de cambios, sin diffs, sin posibilidad de revisar qué cambió entre versiones (los `.md` duplicados con `_ocr` y `-JRJ` son el síntoma).
2. **`.claude/settings.json` con `defaultMode: bypassPermissions`** y permisos amplios (`Bash(bash *)`, `Bash(rm -f ...)`, lectura de todo el home). Cómodo, pero significa que cualquier sesión de Claude puede ejecutar comandos destructivos sin confirmación. Riesgo alto en una máquina con datos de clientes.
3. **Skill `daily-timebox` con el frontmatter YAML duplicado** (el bloque `---name/description---` aparece dos veces) — funciona, pero es frágil; y las instrucciones mezclan configuración (carpeta de trabajo) con reglas de negocio en un texto poco estructurado.
4. **No existe ninguna skill del proyecto MundoSocios:** el contexto vive en `00_HANDOFF_Contexto_Proyecto_MundoSocios.md` (excelente documento) pero cada sesión nueva depende de que alguien recuerde leerlo. La carpeta `ODOO_MUNDOSOCIOS/.claude/` solo contiene un archivo de lock.
5. **Artefactos de desarrollo en OneDrive:** `__pycache__/`, carpeta de proxy duplicada, zips de exportación sueltos en la raíz del proyecto.

### 6.2 Mejoras propuestas

1. **Usar este repositorio como fuente versionada** de todo lo textual y de código: los `.md` (entregables, blueprints, manuales transcritos, handoff), el Validador SII con sus tests, y la configuración del proxy. OneDrive queda para binarios de intercambio con el cliente (.docx/.xlsx/.pptx). Beneficio inmediato: historial, diffs, y sesiones de Claude (web o CLI) que trabajan sobre el estado real.
2. **Crear una skill de proyecto** (`.claude/skills/mundosocios-context/SKILL.md`) que apunte al handoff y resuma las reglas fijas (matriz de aprobaciones, cuentas contables, gotchas de fórmulas Excel en español, estilo de trabajo). Así cualquier sesión nueva arranca con el contexto sin repetir el traspaso manual.
3. **Endurecer `settings.json`:** cambiar `defaultMode` a `acceptEdits` y dejar en `allow` solo lo recurrente y seguro (git, python3, npm); quitar `Bash(bash *)` y los `rm`. El costo son algunas confirmaciones más; el beneficio, que ningún agente pueda borrar/ejecutar sin freno.
4. **Arreglar `daily-timebox`:** un solo frontmatter, y separar "dónde están los archivos" (configuración) de "qué hacer cada día" (pasos numerados con horario).
5. **Añadir un `.gitignore`** (ya incluido en este commit) que excluya `__pycache__`, `.DS_Store`, `~$*` de Office y credenciales, para cuando se migre el código al repo.

---

## 7. Plan de mejoras priorizado

| # | Acción | Bloque | Impacto | Esfuerzo | Depende de |
|---|---|---|---|---|---|
| 1 | Visto bueno escrito de Patricio: Política de Aprobaciones + checklist contra caso real de TXT + checks SharePoint | Fase 0 | Alto | Bajo | Cliente |
| 2 | Contratar API Gateway, primera llamada real del Validador SII, verificar campos JSON | Validador | Alto | Bajo | Cliente (~$10.000/mes) |
| 3 | Corregir `BP_Proceso_Creación_Proveedor.docx` (contenido duplicado de Experiencia) | Flujos | Alto | Bajo | — |
| 4 | Escribir procedimiento de pago a aseguradoras / fondos de terceros (PC-04 crítico) | Flujos | Alto | Medio | Entrevista Oriana/Patricio |
| 5 | Preguntas a Indasoge (hosting, TXT, pasarela, recaudación, Buk) antes de firmar | Odoo | Alto | Bajo | — |
| 6 | Eliminar espejo manual 01→03: fuente única de proveedores + listas desplegables + fecha de refresco | Herramientas | Alto | Medio | — |
| 7 | Registro de aprobación en la 02 (tramo calculado + aprobado por/fecha/evidencia) + alerta en la 03 + control anti-fraccionamiento | Herramientas | Alto | Medio | — |
| 8 | Banner "FUERA DE ALCANCE" en los 4 documentos restantes de Build/ + corregir 00_INDICE (45 tests, API Gateway) | Fase 0 | Medio | Bajo | — |
| 9 | Ejecutar entrevistas E5 → completar E1/E4, quitar "borrador", corregir inconsistencias E1§5/QW3/QW7 | SOW | Alto | Medio | Agenda cliente |
| 10 | Priorización MoSCoW + criterios de aceptación + nativo/config/desarrollo en E3 | SOW | Alto | Medio | #5 |
| 11 | Cartola Banco de Chile en Excel/CSV + script de fecha/validación del TXT | Flujos | Alto | Medio | Banco |
| 12 | Zoho Desk para atención/reembolsos con ticket y estado | Flujos | Alto | Medio | — |
| 13 | Migrar .md + Validador SII a este repo Git; OneDrive solo para binarios de cliente | Entorno | Medio | Medio | — |
| 14 | Skill de proyecto MundoSocios + endurecer settings.json + arreglar daily-timebox | Entorno | Medio | Bajo | — |
| 15 | Higiene OneDrive: __pycache__, proxy duplicado, versiones _ocr/-JRJ, zips en raíz | Entorno | Bajo | Bajo | — |
| 16 | Plan de adopción de las 5 planillas (responsable, fecha, métrica por QW) + sesión de entrenamiento | Herramientas | Alto | Medio | #1 |

---

## 8. Método de esta evaluación

Se leyó el handoff del proyecto (2026-07-06), el análisis de la ficha de Odoo México, la configuración de Claude sincronizada en OneDrive, y —mediante tres revisiones paralelas— los 5 entregables SOW en .md, 15+ documentos de FLUJOS DE PROCESO (blueprints y manuales transcritos) y toda la carpeta Automatización Puente Compras (Fase 0, Build, Herramientas Operativas, Validador SII y proxys). Los binarios .xlsx/.docx/.pptx no se recalcularon; su estado se tomó de la documentación que los describe (verificaciones del 2026-07-02 y 2026-07-06 declaradas en el handoff y el checklist).
