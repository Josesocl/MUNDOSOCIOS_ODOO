# Requerimientos para desarrollar completa la automatización de Recaudación y Cobranza

**Proyecto:** MundoSocios CChC · **Fecha:** 2026-07-31 · **Estado:** checklist de desarrollo
**Dónde vive el proyecto:** repositorio GitHub `Josesocl/MUNDOSOCIOS_ODOO` (rama `claude/project-eval-workflow-2du3as`), carpeta `herramientas/`. Datos fuente: OneDrive `…/MUNDOSOCIOS ODOO/FLUJOS DE PROCESO/RECAUDACIÓN Y COBRANZA/`.
**Documentos base:** `docs/automatizacion-puente/Plan_Automatizacion_Cobro_Recurrente_Puente.md` (plan por olas) · `docs/flujos-proceso/BP_Devengo_Recaudacion_Cobranza_MundoSocios.md` v2.0 (proceso) · `docs/fase-0/Politica_morosidad_y_pagos_parciales_BORRADOR.md`.

---

## 1. Lo que YA está construido (no rehacer)

| Pieza | Ubicación en el repo | Estado |
|---|---|---|
| Generador de devengos de seguros (4 archivos mensuales, UF por seguro, valida RUT/cliente) | `herramientas/generador-devengos/generador_devengos.py` | Construido; montos validados al peso contra JUL-26. **Falta: mes en paralelo** |
| Generador de devengo anual de cuota social (reglas 2026, cuentas verificadas) | `herramientas/generador-devengos/generador_cuota_social.py` | Construido; validado contra ENE-26. **Falta: usarlo en el ciclo ENE-27** |
| Cruzador de pagos (cartola Excel + resumen Transbank + maestro → borrador PRECONCILIACIÓN) | `herramientas/cruzador-pagos/cruzador_pagos.py` | Construido con fixtures de los formatos reales. **Falta: calibración con junio real** |
| 26 pruebas automatizadas | `tests/` de ambas herramientas | Pasando |
| Blueprint v2.0 + diagramas de flujo v2.0 | `docs/flujos-proceso/` | Entregados a revisión MS |

## 2. Insumos y documentos que NECESITAMOS (por responsable)

### Del banco / Transbank (gestiona Marcos o Patricio)
| # | Insumo | Para qué | Bloquea |
|---|---|---|---|
| I-01 | **Rendición PAC por convenio (16 y 41)**: archivo del banco con el detalle por socio de cada abono "Pac Multibanco" | Distribuir la recaudación PAC por socio (hoy llega como monto agregado por banco) | Distribución PAC automática |
| I-02 | **Archivo/reporte de rechazos PAC y PAT** (layout) | Lista automática de rechazados para el correo de cobro y el reintento | Rechazos semi-automáticos |
| I-03 | Acceso/rutina de descarga del reporte Transbank **"Abonos por día"** (detalle de ventas) | Segmentar cada abono por canal (PAT 32606164 / Webpay Plus 51709929 / Webpay.cl 35997075 / QR / POS) en el cruzador v2 | Cruzador v2 |

### De Manager+ (gestiona Oriana o Marcos)
| # | Insumo | Para qué | Bloquea |
|---|---|---|---|
| I-04 | Export del **Exportador de datos**: documentos de CxC / saldos por cliente (layout de columnas) | Cruzar deuda vigente contra pagos → estado real por socio y aging de morosidad | Estado de deuda y morosidad |
| I-05 | Export de **clientes** (RUT, nombre) actualizado | Validación "cliente existe" de los generadores y match de nombres del cruzador | Ya funciona con CSV manual; falta rutina |

### Del equipo MS (Oriana / Carla)
| # | Insumo | Para qué | Bloquea |
|---|---|---|---|
| I-06 | **Maestro único consolidado**: los 6 mantenedores (4 seguros + cuota social empresa/persona) en un solo archivo con RUT, nombre, producto, factor UF/miembros, medio de pago, estado PAC/PAT, cámara, correo | Fuente única de generadores, cruzador y listas de cobranza; después, carga inicial de Odoo | **Todo** (es el insumo central) |
| I-07 | Base **"PAC activos"** (la que comparte Oriana) y su fecha de corte | Completar el maestro con el estado real de convenios | I-06 |
| I-08 | **Textos aprobados** de correos de cobro, recordatorio, rechazo y comunicados de eliminación (los que ya usan) | Plantillas de Zoho Campaigns con métricas | Cobranza con métricas |
| I-09 | La **PRECONCILIACIÓN de junio ya conciliada** (existe en la carpeta) | Calibrar el cruzador comparando su borrador contra el resultado manual | Calibración (sin costo extra) |

### Decisiones / precisiones (Patricio / Constanza / Oriana)
| # | Decisión | Nota |
|---|---|---|
| D-01 | Regla de morosidad de seguros: qué significa el **"9"** (¿meses?, ¿UF?) | Precisión pendiente desde el 2026-07-07 |
| D-02 | UF de cierre **enero/febrero/marzo**: cuál aplica a qué caso de cuota social | Pendiente |
| D-03 | **Política de morosidad y pagos parciales**: validar el borrador (`docs/fase-0/`) | Sin política no hay recordatorios automatizables |
| D-04 | **Control de cumplimiento Addval (48 h)**: registro envío-vs-subida; ¿lo produce el cruzador como subproducto? | Recomendado: sí |
| D-05 | Cuenta/usuario del equipo MS donde correrán las herramientas (Python en un equipo del área, no del consultor) | Regla del proyecto |
| D-06 | Acceso a **Zoho Campaigns** y quién dispara las campañas | Para la Ola 2 |

## 3. Desarrollo restante (con lo anterior en mano)

| # | Entrega | Depende de | Esfuerzo |
|---|---|---|---|
| B-01 | **Calibración del cruzador** contra junio real (umbral de confianza, diccionario nombre→RUT desde la preconciliación histórica) | I-09 | 0,5 día |
| B-02 | **Cruzador v2**: detalle Transbank por código de comercio + estado de deuda por socio + aging de morosidad + CSV de estados para Zoho + paquete Addval + control 48 h | I-03, I-04, D-04 | 2 días |
| B-03 | **Distribuidor PAC**: parser de la rendición por convenio → rebaja propuesta por socio | I-01 | 1 día |
| B-04 | **Rechazos semi-automáticos**: parser de rechazos → lista para campaña + marca de reintento | I-02 | 0,5 día |
| B-05 | **Listas de cobranza para Zoho Campaigns** (deuda vigente / 7-15-30 días / rechazo PAC) generadas por el cruzador + plantillas cargadas | I-08, D-03, D-06 | 1 día |
| B-06 | **Mes en paralelo de los generadores** (devengos de agosto junto al proceso manual, cuadrando totales) | I-06 | operación, no desarrollo |
| B-07 | **Conversor cartola → CONCILIACIÓN MANAGER** (elimina el Excel puente de la conciliación mensual) | formato ya levantado | 1 día |
| B-08 | Manuales de 1 página + entrenamiento al equipo (Marcos/Fran/Oriana) | todo lo anterior | 1 día |

**Total desarrollo restante: ~7 días de construcción**, contra ~50–60 horas/mes de alivio estimado. Nada se pierde: maestro, textos, reglas y datos limpios son insumo directo de Odoo (Suscripciones + Follow-up + conciliación nativa).

## 4. Optimizaciones adicionales detectadas (opcionales, de bajo costo)
- El **control de cumplimiento Addval** sale gratis del cruzador (fecha de envío vs fecha de registro en Manager+) — convierte el plazo de 48 h en un dato medible sin pedir nada a Addval.
- La **segmentación por código de comercio** separa automáticamente recaudación PAT de pagos Webpay dentro del mismo abono diario — hoy indistinguibles en la cartola.
- El **diccionario nombre→RUT** aprendido de las preconciliaciones históricas mejora mes a mes la identificación de transferencias sin trabajo adicional.
- Guardar la **orden de pago Webpay** al generar cada cobro (decisión de diseño para Odoo) es lo único que hará 100% automática la identificación venta→socio en el futuro.

## 5. Secuencia sugerida
1. **Esta semana:** I-06/I-07 (maestro), I-09→B-01 (calibración), D-01/D-02/D-03 (precisiones y política).
2. **Agosto:** B-06 (paralelo de generadores) + I-01/I-02/I-03/I-04 (insumos banco/Manager+) → B-02/B-03/B-04.
3. **Septiembre:** B-05 (Campaigns) + B-07 (conversor) + B-08 (entrenamiento) → operación puente completa hasta Odoo (nov-2026).
