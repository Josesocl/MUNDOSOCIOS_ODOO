# HANDOFF — Proyecto MundoSocios (CChC): Diagnóstico financiero-contable, automatización puente y requerimientos Odoo

> **Propósito de este archivo:** traspasar todo el contexto del trabajo a otra cuenta/sesión de Claude. Es autocontenido: léelo completo antes de continuar. Todos los archivos referenciados están bajo la carpeta raíz del proyecto y sus subcarpetas.

**Carpeta raíz del proyecto (accesible desde la otra cuenta):**
`/Users/jrjottar/Library/CloudStorage/OneDrive-IBSolucionLtda/Documentos OneD IBS/CONSULTORÍA JR JOTTAR/CLIENTES CONSULTORA JRJ/MUNDOSOCIOS ODOO`

**Fecha del handoff:** 2026-06-23 · **última actualización: 2026-07-06**

> **Nota (2026-07-08):** copia migrada al repositorio Git `Josesocl/MUNDOSOCIOS_ODOO`. La versión maestra sigue en OneDrive; si difieren, manda la de OneDrive.

---

## 0. Qué cambió desde el 2026-06-23 (leer primero)

1. **Los 4 entregables del SOW + una guía de entrevistas ya existen en Word**, en `Entregables SOW/` (`.docx`, generados desde los `.md` de §6 con `docx-js`, validados). El Entregable 1 incluye además un anexo con 2 diagramas de flujo AS-IS→TO-BE (Compras/Proveedores y Pago a Proveedores).
2. **Se verificó el COT-2026-MS-001 contra lo entregado: coincide exactamente** (4 entregables, 15 h/45 UF, Constanza Daniels como contacto). No hay nada que corregir ahí.
3. **Los `FICO_MS-001/003.docx` (pre-existentes, §9) ya fueron reconciliados** contra los Entregables 1 y 3: mismo contenido de fondo; se corrigió una discrepancia de fecha (24→23 de junio) en ambos, y se agregó a FICO_MS-003 el requerimiento **RF-06b** (datos bancarios visibles/validados también al pagar, no solo al crear el proveedor) que ya estaba en el Entregable 3 pero faltaba ahí.
4. **Decisión de alcance del cliente (2026-07-06): se descarta construir la capa Zoho CRM** ("sistema puente" — módulos, Blueprint, Approval Process, Deluge en `Automatizacion Puente Compras/Build/` y Fases 1-2 del plan). El cliente solo necesita **verificación de proveedor, aprobación por tramo y carga manual a Manager+**, ya cubierto sin Zoho por `Fase 0/` + `Herramientas Operativas/`. Los documentos de diseño de la capa Zoho quedan con un aviso "FUERA DE ALCANCE" al inicio (no se borraron, son referencia histórica reutilizable si se retoma antes de la migración a Odoo).
5. **`Herramientas Operativas/` (carpeta `Automatizacion Puente Compras/Herramientas Operativas/`) tiene 5 Excel construidos y verificados con recálculo real (LibreOffice, instalado localmente):**
   - `01_Ficha_Proveedor_MundoSocios.xlsx` — checklist con semáforo APTO/EN VALIDACIÓN.
   - `02_Registro_y_Plantilla_OC_MundoSocios.xlsx` — calcula IVA, total y tramo de aprobación automáticamente.
   - `03_Control_Nomina_Pago_MundoSocios.xlsx` — detecta errores que rompen el TXT antes de tocar Manager+; **actualizado 2026-07-06** con una hoja `Proveedores` (espejo de 01) y columnas que cruzan cada pago contra la ficha por RUT (banco/cuenta/estado + alerta de no-coincidencia), cerrando el pendiente del checklist v2.0.
   - `04_Calculo_UF_Cuota_Social_MundoSocios.xlsx` — UF del día en vivo (fórmula nativa Excel 365, sin macros).
   - `05_Conciliacion_Bancaria_MundoSocios.xlsx` — Preconciliación/Conciliación Manager/Cuadratura.
   - `Validador SII (Python standalone)/` — CLI + servidor local para validar RUT/situación tributaria (45 tests). **Migrado 2026-07-06 de BaseAPI a API Gateway** (BaseAPI se discontinúa dic-2026): usa `GET /api/v2/sii/contribuyentes/situacion_tributaria/tercero/{rut}` vía token `APIGATEWAY_API_TOKEN` (sin clave SII propia), costo confirmado con la API de precios real del sitio (~$10.000 CLP/mes fijo + $5 CLP/consulta). Los nombres exactos de los campos JSON de la respuesta siguen sin verificar (no hay token de prueba real). BaseAPI queda como `--proveedor baseapi` (legado). Se evaluó también `mipyme/contribuyentes/info` (traería Dirección) pero exige la clave del portal SII propio de MundoSocios — se descartó por ahora.
6. **Lección técnica importante para seguir construyendo estas planillas:** `XLOOKUP` escrito por `openpyxl` produce `#NAME?` en Excel real (falta el prefijo `_xlfn.` que openpyxl no agrega solo) — usar `INDEX/MATCH` en su lugar. Igual que `TEXTJOIN` (usar `UNIRCADENAS` o mejor `&`), son funciones que cambian de nombre según el idioma de Excel del cliente (español). **Siempre verificar fórmulas nuevas con recálculo real** (headless LibreOffice → leer valores cacheados con `data_only=True`), no basta con que `openpyxl` guarde el archivo sin error.
7. Se generó también una **presentación ejecutiva PPTX** (12 slides) para Constanza Daniels en `Presentacion_Ejecutiva_Gerencia_General/Presentacion Ejecutiva - MundoSocios.pptx`, con los 2 diagramas y las herramientas.
8. **Memoria guardada** (sistema de memoria de Claude, fuera de esta carpeta) sobre la decisión de alcance y las gotchas de fórmulas — otra sesión/cuenta debería heredarla automáticamente si usa el mismo sistema de memoria; si no, este §0 es la fuente de verdad.

---

## 1. Quiénes y qué

- **Consultor:** JR Jottar (IBS Solución), correo de trabajo `jr.jottar@ibsolucion.com` / `jrjottar@ibsolucion.com`.
- **Cliente:** MundoSocios — programa de la Cámara Chilena de la Construcción (CChC). Dominio del cliente: `cchc.cl`.
- **Responsable funcional del cliente:** **Patricio Fernández** (Adm. y Finanzas).
- **Otros interlocutores:** Cecilia Ramírez (OC/compras), Oriana Romero (recaudación), Carla Carvajal / Javiera Valdovinos (incorporación socios), Constanza Daniels (Gerente General).

> **Actualización 2026-07-07:** Javiera Valdovinos ya no está en MundoSocios. Nuevo actor: **Marcos Ibarra**, Analista de Administración y Control de Gestión (envía los cierres diarios a Addval y apoya recaudación).

## 2. Contexto y objetivo del encargo

MundoSocios migrará su ecosistema (Zoho One, Manager+, WordPress, Excel) a **Odoo Enterprise** en ~5 meses. El servicio contratado tiene **doble objetivo**:
1. Levantar y documentar los procesos financiero-contables actuales e identificar automatizaciones inmediatas.
2. Preparar al equipo de finanzas (liderado por Patricio) como aliado estratégico del proyecto Odoo (gestión del cambio).

### El SOW real (importante para el alcance)
Servicio de **15 horas / 45 UF + IVA** (3,0 UF/h), 2-3 semanas. Es **ancho pero liviano**:
- Diagnóstico de **todos** los procesos financiero-contables.
- **Quick wins** simples en herramientas actuales (≈3 h; Excel/macros/plantillas/forms).
- **Coaching / gestión del cambio**.
- **4 entregables** (ver §6).

> **Decisión de alcance clave:** un diseño profundo de "sistema puente" en Zoho CRM (módulos + Blueprint + Deluge) se construyó al inicio, pero **excede las 3 h de quick wins del SOW**. Se **reposicionó como insumo de "Requerimientos Odoo"** (Entregable 3) y como diseño de referencia, NO como algo a implementar dentro de estas 15 h. Los quick wins se acotan a lo liviano.

## 3. Evolución del entendimiento (para no repetir vueltas)

1. Primer pedido: "automatizar compras y proveedores". Se asumió Odoo.
2. Aclaración del cliente: **NO es Odoo todavía**. Primero un **sistema puente** sobre el stack actual; Odoo viene en ~5 meses. El proyecto puede partir hoy (no esperar al 01-jul).
3. Zoho disponible: **solo CRM/Forms/Campaigns** (sin Creator ni Flow).
4. Integración con Manager+: **por archivo export/import, NO API** (decisión del cliente). **Confirmado**: Manager+ tiene `Mantenedores → Importador/Exportador de datos` y ya se usa (carga masiva de devengos vía Excel).
5. El cliente compartió el **SOW presupuestado** → se realineó todo a los 4 entregables (15 h).

## 4. Arquitectura del sistema puente (referencia — reposicionada como requerimientos Odoo)

Tres capas con dueño claro:
- **Zoho CRM** = orquestación y trazabilidad (estado del proceso, expediente, aprobaciones pre-OC, validación SII).
- **Manager+** = registro contable (proveedor formal, OC, factura, CxP, nómina, TXT, conciliación). Se mantiene.
- **SharePoint MundoSocios** = respaldo documental. Zoho guarda solo el link.

Diagrama de las 3 capas: se generó como SVG en el chat (no archivo) y está embebido en Mermaid dentro del diseño (ver §6, archivo de diseño del puente, sección 3).

## 5. Decisiones y restricciones clave

- **Dominio `cchc.cl` NO accesible** para la automatización; el productivo opera con cuentas MundoSocios (SharePoint con cuenta de Patricio). Parametrizar owners/usuarios, nunca cuentas del consultor.
- **Integración Manager+ = archivo (no API)**, mecanismo ya probado (importador de comprobantes Excel con encabezado, valida y reporta errores como "Cliente no existe").
- **Validación SII**: el sitio oficial `www2.sii.cl/stc/noauthz` / `zeus.sii.cl` tiene fila + captcha → no automatizable directo. Fase 1 = manual-asistida; Fase 2 = **API REST de terceros** (candidatos: BaseAPI `baseapi.cl`, API Gateway `apigateway.cl`).
- **Matriz de aprobaciones (paramétrica, CLP bruto c/IVA):**
  | Tramo | Aprobador |
  |---|---|
  | Hasta 500.000 | Dueño del presupuesto (por centro de costo) |
  | 500.001 – 1.000.000 | Cecilia Ramírez |
  | 1.000.001 – 5.000.000 | Patricio Fernández |
  | Sobre 5.000.000 | Doble firma: Patricio Fernández + Constanza Daniels |

## 6. Índice de archivos generados EN ESTA SESIÓN (rutas relativas a la carpeta raíz §0)

> Todos los archivos de esta sección son `.md` creados en esta sesión de Claude. El material pre-existente en la carpeta (cotizaciones, propuestas de partners Odoo, manuales transcritos, etc.) se lista aparte en §9.

### Entregables del SOW — `Entregables SOW/`
- `Entregables SOW/1 - Informe de diagnostico procesos financiero-contables.md` — diagnóstico completo: inventario de herramientas, mapa de **13 subprocesos**, **13 puntos críticos**, conclusiones para la migración.
- `Entregables SOW/2 - Plan de automatizaciones inmediatas (quick wins).md` — 8 quick wins con matriz impacto/esfuerzo, acotados a las ~3 h.
- `Entregables SOW/3 - Documento de requerimientos para Odoo (area financiera).md` — 24 requerimientos (RF-01…RF-24) mapeados a módulos Odoo + integraciones + datos a migrar.
- `Entregables SOW/4 - Reporte de gestion del cambio.md` — disposición, riesgos, estrategia (Patricio como key user), plan de 3 sesiones.

### Diseño del sistema puente — `Automatizacion Puente Compras/`
- `Automatizacion Puente Compras/2026-06-18-automatizacion-compras-proveedores-design.md` — spec de diseño (3 capas, flujo, matriz §5.1, operación productiva §8.1, riesgos). Incluye diagrama Mermaid.
- `Automatizacion Puente Compras/2026-06-18-plan-implementacion-compras-proveedores.md` — plan por fases (0,1,2,cierre), ~25 tareas con criterios de aceptación.
- `Automatizacion Puente Compras/2026-06-18-cronograma-y-responsables.md` — fases, responsables, hitos bloqueantes.

#### Fase 0 (entregables listos para usar) — `Automatizacion Puente Compras/Fase 0/`
- `.../Fase 0/Politica de aprobaciones de compras.md`
- `.../Fase 0/Checklist campos criticos del proveedor.md`
- `.../Fase 0/Convencion de carpetas SharePoint.md`
- `.../Fase 0/Formulario Zoho - Solicitud de Compra.md`
- `.../Fase 0/Plantilla Orden de Compra.md`

#### Build (especificaciones técnicas) — `Automatizacion Puente Compras/Build/`
- `.../Build/Especificacion modulos Zoho CRM.md` — módulos, campos, picklists, estados Blueprint.
- `.../Build/Borradores Deluge.md` — funciones `resolverAprobador`, `validarSII`, `exportarProveedorManager`, `exportarOCManager`.
- `.../Build/00_INDICE - Guia de implementacion.md` — punto de entrada del paquete Zoho.
- `.../Build/Workflow Rules - Alertas y Recordatorios.md`
> **Toda la carpeta `Build/` y las Fases 1-2 del plan quedan marcadas "FUERA DE ALCANCE" desde 2026-07-06 — ver §0.4.**

#### Generado después del 2026-06-23 (sesiones posteriores)
- `Entregables SOW/1..4 - *.docx` y `5 - Guia de entrevistas.(md/docx)` — versión Word de los 4 entregables + guía de entrevistas nueva.
- `Entregables SOW/FICO_MS-001*.docx`, `FICO_MS-003*.docx` — reconciliados con los Entregables 1 y 3 (ver §0.3).
- `Presentacion_Ejecutiva_Gerencia_General/Presentacion Ejecutiva - MundoSocios.pptx` — 12 slides para Constanza Daniels.
- `Automatizacion Puente Compras/Herramientas Operativas/01_Ficha_Proveedor_MundoSocios.xlsx`
- `Automatizacion Puente Compras/Herramientas Operativas/02_Registro_y_Plantilla_OC_MundoSocios.xlsx`
- `Automatizacion Puente Compras/Herramientas Operativas/03_Control_Nomina_Pago_MundoSocios.xlsx` — incluye hoja `Proveedores` y cruce bancario (2026-07-06).
- `Automatizacion Puente Compras/Herramientas Operativas/04_Calculo_UF_Cuota_Social_MundoSocios.xlsx`
- `Automatizacion Puente Compras/Herramientas Operativas/05_Conciliacion_Bancaria_MundoSocios.xlsx`
- `Automatizacion Puente Compras/Validador SII (Python standalone)/` — `cli.py`, `server.py`, `sii_client.py`, `rut_utils.py`, `html_report.py`, `tests/`.

### Materiales fuente (levantamiento del cliente) — `SHAREPOINT_ODOO/`
- `SHAREPOINT_ODOO/Resumen Flujos Cotización Inicial Odoo.docx`
- `SHAREPOINT_ODOO/Levantamiento Adm. y Finanzas/Flujo de Compras 15-06-26.docx`
- `SHAREPOINT_ODOO/Levantamiento Adm. y Finanzas/Plan_de_cuentas_con_niveles_MS 2026.xlsx`
- `SHAREPOINT_ODOO/Levantamiento Adm. y Finanzas/MundoSocios_Cuota Social 2026.xlsx`
- `SHAREPOINT_ODOO/Levantamiento Adm. y Finanzas/Flujos y Manuales Adm. y Finanzas/` — 14 manuales PDF (compras, cotizaciones, creación de proveedores y de clientes, ingreso de facturas y de boletas, nóminas de pago y de rendiciones, conciliación, cobranza cuota social, devengo cuota social, carga de devengos, solicitud de sala/alimentación, pasajes/alojamiento).

## 7. Resumen del diagnóstico (procesos y dolores)

### Stack actual
Zoho One (CRM/Forms/Campaigns), Manager+ (ERP contable, con Importador/Exportador), Acepta/Sovos (recepción DTE), Banco de Chile (cta. 8001104309, TXT), Webpay, Google Sheets (varias planillas paralelas), Excel, OneDrive/SharePoint, Outlook, SII (web), WordPress. Proveedores de servicio: Aramark (alimentación), Travel Security / Chicureo Travel (pasajes), hoteles.

### Procesos mapeados (13)
Compras/cotizaciones · proveedores · facturas (Acepta→SII→Manager, con/sin OC) · boletas de honorarios (retención 13,75%) · nóminas de pago proveedores (martes, TXT) · rendiciones equipo + nómina de personal (2º TXT) · conciliación bancaria (mensual, ~233 mov./cartola, ~78% auto) · recaudación cuota social (~1.500 notas de cobro/mes) · devengo cuota social · carga de devengos de seguros (fondos de terceros) · fondos propios vs. terceros · creación clientes/socios · solicitudes internas (sala/alimentación/pasajes/alojamiento).

### Dolores raíz
1. **TXT bancario frágil**: campos vacíos en maestro de proveedor, caracteres especiales, descripción >400, NC/anticipos en negativo, tipo de documento; además la **fecha de pago se edita a mano** en el TXT.
2. **Conciliación** dependiente de planillas Excel intermedias (preconciliación/conciliación manager); casos PAC y devengos sin OT.
3. **Doble registro**: planillas Drive paralelas a Manager+; formulario web no integrado al CRM.
4. **Dependencia de personas** (Cecilia, Carla, etc.).
5. **UF y validación SII manuales**.
6. **Separación fondos propios/terceros** sostenida manualmente (riesgo alto).
7. **Dos TXT** (proveedores y personal) y múltiples planillas Drive como control de facto.

### Detalle contable útil
- Devengo cuota social: comprobante Traspaso, DEBE `1150001 Cuota S. Empresa por Cobrar` (doc CSEMP) / HABER `3210002 Cuota Social Empresa`.
- Devengos de seguros (fondos de terceros), cuentas por cobrar/ingreso: Plan Socios 1130004/3310005, Complementario 1130003/3310003, Catastrófico 1130002/3310001, Plan Carreño 1130005/3310004.
- Cuota social: Empresa 1,44 UF / Persona 0,48 UF (UF del día desde el SII).

> **Corrección 2026-07-07 (verificada contra archivos productivos ENE-26/JUL-26):** los valores 1,44/0,48 UF están desactualizados. Cuota social 2026: **Persona 1 UF (DEBE 1150002 / HABER 3210001, doc CSPER)** · **Empresa 3 UF hasta 3 miembros + 1 UF por miembro desde el 4º (DEBE 1150001 / HABER 3210002, doc CSEMP)**, devengo anual único al 1 de enero, CC contrapartida ADM. Seguros: CC contrapartida MS, Conceptos 1/2 = 99999/500; el complementario usa la UF del día 9 y el catastrófico la UF del último día del mes anterior. Ver `.claude/skills/mundosocios-context/SKILL.md` del repositorio.

## 8. Estado actual y próximos pasos sugeridos

**Hecho (actualizado 2026-07-06):** los 4 entregables del SOW + guía de entrevistas, en `.md` y `.docx`; 2 diagramas de flujo AS-IS→TO-BE incorporados al diagnóstico; presentación ejecutiva PPTX; 5 herramientas Excel operativas verificadas con recálculo real; Validador SII standalone; FICO_MS-001/003 reconciliados; documentos de la capa Zoho CRM marcados como fuera de alcance (ver §0).

**Pendientes a confirmar con el cliente (entrevistas — usar `Entregables SOW/5 - Guia de entrevistas`):**
- Caja chica, ajustes de CxP (anticipos/NC), morosidad y pagos parciales.
- Volúmenes/tiempos por proceso y composición del equipo.
- Centros de costo y su "dueño de presupuesto"; usuarios Zoho de los aprobadores (solo relevante si se retoma la capa Zoho).
- Layout exacto de archivos de Manager+ para automatizar más allá de devengos.
- Validación por escrito de Patricio de la política de aprobaciones (`Fase 0/Politica de aprobaciones de compras.md`, sigue en estado "borrador").
- Decisión de contratar BaseAPI (o alternativa) para que el Validador SII deje de ser manual-asistido.

**Próximos pasos posibles:**
- Agendar las 3 sesiones de gestión del cambio con Patricio/equipo (Entregable 4).
- Entrenar a Patricio/equipo en el uso semanal de las 5 herramientas Excel (flujo: 01→02→03→05, más 04 para incorporaciones de socios).
- Si el cliente decide retomar la capa Zoho CRM más adelante, todo el diseño en `Build/` y los planes de Fases 1-2 siguen listos para implementar (solo requieren quitar el aviso "fuera de alcance").

## 9. Material PRE-EXISTENTE en la carpeta (no generado en esta sesión)

Hay trabajo previo relevante en la carpeta raíz que conviene revisar; puede contener decisiones o cotizaciones que esta sesión no consideró en detalle:

- **`PROPUESTA JRJ/`** — Cotizaciones formales del consultor: `COT-2026-MS-001_Procesos_Financieros_MundoSocios.(docx/pdf)` y `COT-2026-MS-002_Acompanamiento_Odoo_MundoSocios.(docx/pdf)`; ficha de proveedor MundoSocios. **El SOW resumido en §2 corresponde a estas cotizaciones — leerlas para el detalle de horas/UF.**
- **`DOCUMENTOS/ODOO WEB Y PARTNERS/`** — Propuestas técnico-económicas de partners Odoo: `CM-R-006 [S00322] Propuesta técnica-económica Odoo - Mundo Socios`, `Presupuesto - S03887.pdf`, `Resumen Flujos Cotización Inicial Odoo.pdf`.
- **`DOCUMENTOS/ODOO MEXICO/`** — `[Mundo Socios] Ficha de Requerimientos.xlsx` (y copia) + `Odoo Brochure.pdf`. **Ficha de requerimientos Odoo de un partner — cruzar con el Entregable 3.**
- **`FLUJOS DE PROCESO/`** — **Todos los manuales del cliente ya transcritos a `.md`** (y OCR), incluido `Plan_implementacion_ODOO mundosocios.docx` y `Resumen Flujos Cotización Inicial Odoo.md`. Útil: en vez de leer los PDF, se pueden leer estos `.md`.
- **`Perplexity_Odoo_MundoSocios/`** — Borradores de plan de implementación Odoo y "siguientes pasos" generados con Perplexity. Material de apoyo, contrastar antes de usar.
- **`Entregables SOW/FICO_MS-001_2026_Procesos_Financieros_MundoSocios.docx`** y **`FICO_MS-003_2026_Documentos_Finanzas_Odoo.docx`** — no generados originalmente en la sesión del 23-jun, pero **ya reconciliados el 2026-07-06** contra los Entregables 1 y 3 (ver §0.3). Sin contradicciones pendientes.
- **`SHAREPOINT_ODOO/2026 1er Trimestre/`** — Estados financieros reales (balance tributario, EERR por mes, flujo de caja, cierre 1er trimestre 2026). Datos contables reales para dimensionar.
- **`SHAREPOINT_ODOO/Levantamiento Adm. y Finanzas/Documentos Flujo de Compras/`** — Formularios reales en PDF (OC, cotización, boleta honorarios, pasajes/estadía, bodega, envío), correo de apoderados e informe de conciliación de abril. Insumos para las plantillas.
- **`BASES DATOS Y ARCHIVOS/Directorio Personas Mundo Socios.xlsx`** — Directorio del equipo.

> **Recomendación para la otra cuenta:** antes de generar nuevo contenido, revisar `PROPUESTA JRJ/` (alcance real), los `FICO_MS-*.docx` en `Entregables SOW/` y la ficha de requerimientos de `DOCUMENTOS/ODOO MEXICO/` para alinear y no duplicar.

## 10. Notas de acceso/operación
- El conector M365/SharePoint del consultor está en el tenant `nubatechcorp`, **no** alcanza el SharePoint de CChC (`cchccl`). Los materiales se trabajaron desde **copia local** en la carpeta `SHAREPOINT_ODOO/`.
- Estilo de trabajo del consultor: respuestas cortas y directas, sin relleno, sin emojis, sin documentación innecesaria salvo que se pida.
