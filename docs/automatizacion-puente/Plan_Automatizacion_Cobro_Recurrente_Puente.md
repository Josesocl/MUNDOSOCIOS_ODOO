# Plan de automatización puente — Cobro recurrente (cuota social + seguros)

**Proyecto:** MundoSocios CChC · **Fecha:** 2026-07-07 · **Horizonte:** julio → noviembre 2026 (Odoo no estará productivo antes de noviembre)
**Objetivo:** reducir el trabajo manual del ciclo devengo → cobro → registro → conciliación con el stack actual, sin construir nada que se bote al migrar: **cada pieza del puente es también insumo de la migración a Odoo**.

**Restricciones de diseño:**
- Zoho disponible: **CRM, Forms, Campaigns** (sin Creator ni Flow). **Actualización 2026-07-07:** Zoho se reabrió parcialmente vía soporte oficial (Alexander Gutiérrez): hay Sandbox con datos productivos, módulo de Proveedores activado, y se acordó validación de RUT por función personalizada e integración SII vía API Gateway. Las automatizaciones de CRM que Alexander construya (reglas de validación, funciones) SÍ están disponibles para este plan; lo que sigue fuera es construir la capa completa de módulos/Blueprint del diseño puente de compras.
- Manager+: **solo por archivo** (Importador/Exportador de datos). Sin API.
- Herramientas nuevas: Excel sin macros o Python simple (stdlib + openpyxl), operables por el equipo de Patricio con manual de 1 página; corren con cuentas MundoSocios, nunca del consultor.
- Banco de Chile: cartola y archivos de nómina por el portal.

---

## 1. El ciclo hoy y dónde se va el tiempo

| Etapa | Hoy | Horas/mes est. | Dolor |
|---|---|---|---|
| Devengo seguros (mensual) | Copiar 4 Excel del mes anterior, editar 22 columnas a mano, importar, corregir "Cliente no existe" | 6–10 h | PC-06 |
| Devengo cuota social (incorporaciones) | UF manual del SII + correo a mano + comprobante manual + ticket Zoho + aviso a Atención (~8 pasos, 4 sistemas por socio) | 4–8 h | PC-03 |
| Cobro y comunicación | Nóminas PAC/PAT + correos de cobro y de rechazo uno a uno, sin métricas | 8–12 h | PC-05 |
| Cruce de pagos | Oriana revisa 3 fuentes (Manager+, Zoho, Excel) cada semana | ~40 h | PC-01 |
| Registro Addval | Marcos Ibarra (Adm. y Control de Gestión) envía el cierre diario (L-V); Addval tiene 48 h para subir a Manager+ (ej.: cierre del 06-jul enviado el 07 → plazo jue 09) | (externo) | PC-02 |
| Conciliación | Cartola PDF → transcripción → PRECONCILIACIÓN → CONCILIACIÓN MANAGER → importar | 8–12 h | PC-07 |
| Morosidad | No existe proceso | — | PC-08 |

## 2. Arquitectura del puente: un maestro y tres archivos que van y vienen

```
                    ┌─────────────────────────────┐
                    │ MAESTRO ÚNICO (SharePoint)   │
                    │ socios + pólizas + medio pago│
                    └──────┬───────────┬──────────┘
             genera        │           │ listas
                           ▼           ▼
   ┌─────────────┐  Generador de   Zoho CRM /
   │ Manager+    │◄─ devengos      Campaigns ──► correos de cobro,
   │ (importador)│   (4 xlsx)      (import CSV)   recordatorio y rechazo
   └──────┬──────┘                                 con métricas
          │ exportador (saldos/documentos)
          ▼
   ┌──────────────────────────────────────────────┐
   │ CRUZADOR DE PAGOS (Python, semanal)          │
   │ entradas: cartola CSV + reporte Webpay +     │
   │ export Manager+ + maestro                    │
   │ salidas: estado deuda por socio · pagos no   │
   │ identificados · paquete Addval · CSV estados │
   │ para Zoho · aging de morosidad               │
   └──────────────────────────────────────────────┘
```

**Regla:** los datos maestros viven en UN archivo en SharePoint (no en 4 mantenedores + planillas paralelas). Todo lo demás se **genera** desde ahí.

## 3. Olas de implementación

### Ola 0 — Desbloqueos (semana del 7 de julio, sin construcción)

Estado 2026-07-07: 0.2 y la mitad de 0.3 quedaron resueltas con la carpeta `FLUJOS DE PROCESO/RECAUDACIÓN Y COBRANZA` (cartola ya viene en Excel/HTML; layouts de cartola, preconciliación, Transbank, devengos y mantenedores levantados y verificados).

| # | Acción | Responsable | Estado / nota |
|---|---|---|---|
| 0.1 | **Consolidar el maestro único** desde los 6 mantenedores (4 seguros + cuota social empresa/persona): rut, nombre, seguro/tipo, factor_uf o miembros, medio de pago, estado PAC/PAT, cámara | Oriana/Marcos + consultor | Los mantenedores reales ya tienen todo el dato; es consolidación, no levantamiento |
| 0.2 | ~~Cartola en Excel/CSV~~ | — | **Resuelto**: la cartola ya se descarga en formato tabla (HTML/.xls) y el cruzador la lee directo |
| 0.3 | **Layouts pendientes**: rendición PAC del banco por convenio (16/41) para distribuir la recaudación PAC por socio, archivo de rechazos PAC/PAT, y qué permite el Exportador de datos de Manager+ | Marcos + consultor | Cartola/Transbank/devengos ya levantados; falta solo lo del banco y Manager+ |
| 0.4 | **Formalizar el ciclo Addval ya existente**: Marcos envía el cierre diario (L-V) y Addval tiene 48 h para subirlo. Falta: registro de cumplimiento (fecha envío vs fecha subida) para hacer exigible el plazo | Marcos | El cruzador puede producir el control de cumplimiento como subproducto |
| 0.5 | **Validar la política de morosidad** (borrador en `docs/fase-0/`) alineada al ciclo real: morosos de cuota social desde mayo, comunicados y eliminación el 1 de julio, reincorporación pagando el año en curso | Constanza/Oriana | Ajustar el borrador con este ciclo anual antes de firmarlo |

### Ola 1 — Devengo sin digitación (julio–agosto)

| # | Entrega | Qué automatiza | Estado |
|---|---|---|---|
| 1.1 | **Generador de devengos** en producción: correr agosto **en paralelo** al proceso manual (comparar totales y filas al azar), septiembre ya solo generador | Los 4 Excel mensuales + validación previa de RUT/clientes (PC-06) | **Construido y testeado** (`herramientas/generador-devengos/`) |
| 1.2 | **Incorporaciones semi-automáticas**: correo de bienvenida/cobro generado desde `04_Calculo_UF` ampliado — se ingresa RUT/tipo/cámara y produce el texto completo del correo (monto UF del día, datos de transferencia, enlace Webpay) para pegar/enviar; y **plantilla de correo en Zoho CRM** con esos campos | UF manual + redacción del correo (PC-03); de ~8 pasos a ~4 | Ampliar planilla 04 (2–3 h, sin macros) |
| 1.3 | **Checklist de incorporación** en la misma planilla: cliente creado en Manager+ → comprobante (glosa estándar generada por fórmula: `RUT DEVENGO CUOTA AÑO CÁMARA`) → ticket Zoho → aviso a Atención | Pasos olvidados entre 4 sistemas | Incluido en 1.2 |

### Ola 2 — Cruce de pagos y comunicación con métricas (agosto–septiembre)

| # | Entrega | Qué automatiza |
|---|---|---|
| 2.1 | **Cruzador de pagos (Python, semanal)** — la pieza mayor del puente. Entradas: cartola CSV, reporte Webpay, export de documentos CxC de Manager+, maestro. Salidas: (a) estado de deuda por socio; (b) pagos no identificados con sugerencia de match por RUT/monto; (c) **paquete Addval** estandarizado del viernes; (d) **CSV de estados para Zoho** (import masivo: "Cuota al día"/"Moroso"); (e) **aging de morosidad** 7/15/30/60 por producto | Las ~10 h/semana de cruce de 3 fuentes (PC-01); la actualización manual de estados en Zoho; el insumo de morosidad (PC-08) |
| 2.2 | **Cobranza por Zoho Campaigns**: listas segmentadas generadas por el cruzador (deuda vigente / 7d / 15d / rechazo PAC) + plantillas aprobadas de la política de morosidad. Campaigns entrega aperturas/clics/rebotes | Correos uno a uno; cierra PC-05 (hoy cero métricas) |
| 2.3 | **Rechazos PAC/PAT semi-automáticos**: el cruzador lee el archivo de rechazos del banco y produce la lista para la campaña de rechazo + marca reintento a 5 días | Correos de rechazo manuales |
| 2.4 | **Generador de nómina PAC/PAT** desde el maestro + deuda vigente (si el layout de 0.3 lo permite) | Armado manual de la nómina de cargos |

### Ola 3 — Conciliación asistida y preparación Odoo (octubre)

| # | Entrega | Qué automatiza |
|---|---|---|
| 3.1 | **Conversor cartola CSV → formato "CONCILIACIÓN MANAGER"**: genera el archivo de importación de Manager+ directo desde la cartola, con la cuadratura (Abono = Otros Abonos + Depósitos) calculada | Los 2 Excel puente y la transcripción (parte de PC-07) |
| 3.2 | **Informe mensual de fondos de terceros**: recaudado vs pagado a aseguradoras por seguro, desde el cruzador + nóminas de pago | El control crítico PC-04 que hoy no existe como reporte |
| 3.3 | **Congelar y limpiar el maestro para la migración**: el maestro del puente = carga inicial de Odoo (contactos + suscripciones + pólizas). Validación final de RUTs/correos | Evita limpiar los datos dos veces |
| 3.4 | Corte de operación: definir con el partner qué período se devenga por última vez en Manager+ y cuál nace en Odoo (DP-08) | — |

## 4. Qué NO se automatiza en el puente (y por qué)

- **Cargo PAC/PAT directo desde Zoho o Python**: requiere integración con pasarela (Toku/Nuvei) — es exactamente el desarrollo crítico de Odoo; hacerlo dos veces no paga por 3 meses.
- **Construcción propia de workflows/Deluge en Zoho CRM**: lo que se haga en Zoho lo construye el soporte oficial (Alexander Gutiérrez) en el Sandbox — validación de RUT, módulo de Proveedores, integración SII vía API Gateway. El diseño de referencia en `Build/` y el Validador SII sirven como especificación para él (ya se acordó enviarle el validador). Este plan no duplica ese trabajo.
- **Registro contable automático de pagos en Manager+**: el importador de comprobantes lo permitiría, pero el registro es la función contratada a Addval — primero exigir el SLA (0.4); si Addval no cumple en agosto, evaluar internalizar usando el paquete del cruzador como archivo de importación.

## 5. Esfuerzo y beneficio

| Herramienta | Construcción | Ahorro estimado | Dolores |
|---|---|---|---|
| Maestro único (0.1) | 1 día (una vez) | habilita todo | — |
| Generador de devengos (1.1) | listo | 6–10 h/mes | PC-06 |
| Planilla incorporaciones + plantilla Zoho (1.2–1.3) | 0,5 día | 3–6 h/mes | PC-03 |
| Cruzador de pagos (2.1) | 3–4 días | **~30 h/mes** | PC-01, PC-08 |
| Campaigns + rechazos (2.2–2.3) | 1 día + textos | 4–8 h/mes y visibilidad | PC-05 |
| Conversor cartola (3.1) | 1 día | 4–6 h/mes | PC-07 parcial |
| **Total** | **~7 días de construcción** | **~50–60 h/mes** | 6 de los 8 PC |

Los dos PC que el puente no resuelve del todo: PC-04 (separación de fondos queda como **reporte** mensual, la separación estructural la da Odoo) y PC-07 (los match N:1 de convenios PAC siguen manuales; Odoo los trae nativos).

## 6. Riesgos del puente

| Riesgo | Mitigación |
|---|---|
| El maestro único no se mantiene (vuelven los 4 mantenedores) | Dueño único (Oriana), archivo en SharePoint con control de versiones, y el generador falla ruidosamente si el maestro tiene errores |
| Layouts del banco/Webpay distintos a lo asumido | Ola 0.3 los levanta ANTES de construir el cruzador |
| Adopción: herramientas nuevas en paralelo al trabajo diario | Un mes en paralelo por herramienta, manual de 1 página, y las 3 sesiones de gestión del cambio del Entregable 4 usan estas herramientas como contenido |
| Sobre-inversión en algo que muere en noviembre | Todo lo construido es maestro de datos, textos de correo aprobados o validadores — insumo directo de Odoo. Nada de UI, nada de integraciones desechables |

## 7. Secuencia resumida

- **Semana 7-jul:** Ola 0 completa (maestro, cartola CSV, layouts, SLA Addval, política).
- **Agosto:** devengo paralelo con generador · planilla de incorporaciones en uso · cruzador v1 con datos reales.
- **Septiembre:** devengo solo con generador · cruzador semanal operando · primera campaña de cobranza con métricas · rechazos semi-automáticos.
- **Octubre:** conversor de cartola · informe fondos de terceros · maestro congelado y limpio para el partner.
- **Noviembre:** corte y arranque Odoo con datos ya limpios y política de morosidad ya validada en producción.

---

**Decisiones que necesito del cliente para partir:** 0.2 (cartola CSV), 0.4 (SLA Addval) y 0.5 (política de morosidad). El resto es construcción del consultor con 1 h de levantamiento (0.3).
