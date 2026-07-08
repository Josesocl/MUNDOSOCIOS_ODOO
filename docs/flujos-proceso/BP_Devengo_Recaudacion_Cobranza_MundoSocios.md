# Blueprint — Devengo, Recaudación, Cobranza y Conciliación

**Cuota Social y Primas de Seguros — Insumo para Odoo Enterprise**
**Proyecto:** Implementación Odoo Enterprise — MundoSocios CChC · **Fase:** Fase 0 — Levantamiento y Diseño
**Fuentes:** Oriana Romero (Recaudación), Patricio Fernández (Adm. y Finanzas), Marcos Ibarra (Adm. y Control de Gestión), manuales operativos, archivos productivos de `FLUJOS DE PROCESO/RECAUDACIÓN Y COBRANZA/`
**Elaborado por:** JR Jottar Consultoría · **Versión:** 2.0 — 2026-07-08 · Borrador para validación

### Registro de cambios v2.0 (respecto de v1.0, julio 2026)
1. Valores y cuentas de cuota social corregidos y **verificados contra los archivos productivos** (`DEVENGO CUOTA SOCIAL * ENE-26.xlsx`).
2. UF diferenciada por seguro (día 9 / último día del mes anterior) según capacitación Oriana→Marcos (2026-07-07).
3. Ciclo real de Addval documentado (envío diario L-V por Marcos Ibarra, plazo 48 h).
4. Nueva sección de morosidad y eliminación (ciclo anual real) y de gestión PAC/PAT (rechazos, reintentos, cambio de tarjeta).
5. Actores actualizados: sale Javiera Valdovinos; entran Marcos Ibarra y Fran (apoyo cobranza).
6. Herramientas puente construidas y validadas (generadores de devengos y cruzador de pagos) referenciadas.

---

## 1. Contexto y dimensionamiento

Proceso de mayor complejidad operativa de MundoSocios: generación masiva de deuda (devengo), recaudación de cuotas sociales y primas de seguros, y conciliación bancaria. Es el que más horas manuales consume (~40 hrs/mes) y el de mayor riesgo contable por la separación de fondos propios y de terceros.

### 1.1 Volúmenes operativos
| Concepto | Volumen | Frecuencia |
|---|---|---|
| Socios titulares | ~1.955 (1.516 Empresa + 439 Persona) | Base |
| Personas con familias | ~4.800 | Base |
| Notas de cobro mensuales | ~1.500 | Mensual |
| Devengo anual cuota social | 650 empresas + 431 personas (ENE-26) | Anual |
| Movimientos por cartola | ~233 | Mensual |
| Cámaras regionales | Múltiples (Santiago, O'Higgins, Maule, Atacama, Pta. Arenas, etc.) | Base |

### 1.2 Productos recurrentes (verificado contra archivos productivos)

| Producto | Tipo fondo | Cobro | Valor | Cta. x cobrar | Cta. ingreso | Doc. | CC contrapartida | Conceptos 1/2 |
|---|---|---|---|---|---|---|---|---|
| Cuota Social Empresa | Propio | **Anual** (devengo único 1 de enero) | **3 UF hasta 3 miembros + 1 UF por miembro desde el 4º** | 1150001 | 3210002 | CSEMP | ADM | — |
| Cuota Social Persona | Propio | **Anual** | **1 UF** | **1150002** | **3210001** | CSPER | ADM | — |
| Seguro Plan Socios | Terceros | Mensual | factor UF × UF | 1130004 | 3310005 | PSOC | MS | 99999/500 |
| Seguro Complementario | Terceros | Mensual | factor UF × **UF del día 9** | 1130003 | 3310003 | SCOMP | MS | 99999/500 |
| Seguro Catastrófico | Terceros | Mensual | factor UF × **UF del último día del mes anterior** | 1130002 | 3310001 | SCAT | MS | 99999/500 |
| Plan Carreño | Terceros | Mensual | factor UF (0,2/0,4/0,6) × UF | 1130005 | 3310004 | PCARR | MS | 99999/500 |

**Regla UF cuota social:** se consideran las UF de cierre de enero/febrero/marzo (☐ precisar con Patricio cuál aplica a qué caso; el devengo ENE-26 real se generó con UF $39.731,77 al 1 de enero).

> Los valores "Empresa 1,44 UF / Persona 0,48 UF" de documentos anteriores están **desactualizados**.

### 1.3 Mix de pago
| Producto | PAC/PAT | Webpay/Transferencia |
|---|---|---|
| Seguros (primas) | ~80% | ~20% |
| Cuota social | ~20% | ~80% |

**Códigos de comercio Transbank** (detalle confirmado por el cliente, 2026-07-08). Cuenta de abono: Banco de Chile 8001104309.

| Código | Canal | Estado |
|---|---|---|
| 32606164 | **PAT** (cargo automático en tarjeta) | Activo |
| 51709929 | **Webpay Plus** (pagos en línea) | Activo |
| 35997075 | **Webpay.cl** (portal de pagos) | Activo |
| 38323415 | **Cobro QR** | Activo |
| 47630680 | **Máquina** (POS presencial) | Activo |
| 35171665 | Máquina — equipo móvil | Inactivo |

> Uso operativo: en los reportes de Transbank ("Abonos por día" / detalle de ventas) el código de comercio permite **segmentar cada venta por canal** — en particular separar la recaudación PAT (32606164) de los pagos Webpay (51709929/35997075) y de los cobros presenciales, algo que la glosa de la cartola no distingue (todos llegan como un único abono "Transbank 0966893109" diario).

### 1.4 Actores del proceso
- **Oriana Romero** (Recaudación): gestiona el ciclo completo de recaudación y cobranza.
- **Marcos Ibarra** (Analista Adm. y Control de Gestión): envía a Addval el cierre diario de transacciones (L-V); apoyo a recaudación (capacitado por Oriana, 2026-07-07).
- **Fran** (apoyo cobranza): barrido de pagos Webpay/transferencias, respuesta a socios (c/c Oriana), llamadas de cobro, comunicados de eliminación, bajas/cambios de tarjeta.
- **Addval** (externo): sube los registros a Manager+ **todos los días de lunes a viernes**, con **hasta 48 horas de plazo** desde el envío (ej.: cierre del 06-jul enviado el 07 → plazo jueves 09). Rebaja la deuda del socio.
- **Carla Carvajal** (Atención/incorporaciones): informa nuevos socios; gestiona beneficiarios y traspasos de cuota entre empresas.
- **Patricio Fernández** (Adm. y Finanzas): supervisión contable, aprobación de pagos, inscripción de nóminas en banco.

> Javiera Valdovinos ya no está en MundoSocios ni en el proceso.

## 2. Situación actual (AS-IS)

### 2.1 Devengo — Cuota social
- **Devengo anual masivo (enero):** desde los mantenedores `Mantenedor Cuota Social empresa/persona.xlsx` se generan los archivos de importación de 22 columnas (`DEVENGO CUOTA SOCIAL EMPRESA/PERSONA ENE-26.xlsx`) y se cargan por el Importador de Manager+. Glosa detalle `{RUT} CE|CP {AA} {CÁMARA}`; contrapartida con CC ADM.
- **Incorporaciones durante el año:** Carla informa por correo → se calcula la cuota (regla §1.2, con prorrateos manuales cuando aplica) → correo al socio con datos de transferencia (Corporación de Bienestar y Salud, RUT 65.091.028-1, Banco de Chile 8001104309) y enlace Webpay → al pagar: cliente en Manager+, comprobante de Traspaso, ticket de cuota en Zoho, aviso a Atención.

### 2.2 Devengo — Seguros (mensual masivo)
Mantenedores por seguro (`MANT. * 07-26.xlsx`) con: medio de pago (PAC/PAT/DIRECTA/EMPRESA), RUT, nombre, inicio de cobertura, factor UF, estados PAC/PAT ("ACTIVO"/"no cargar"), fila de UF por mes y columnas mensuales valorizadas. De ahí se construyen los archivos de importación de 22 columnas (A–V) con contrapartida final (cuenta de ingreso, CC MS, total en HABER). Si un RUT no existe como cliente, el importador rechaza con "Cliente no existe".

**Puente construido (2026-07-07):** los generadores del repositorio (`herramientas/generador-devengos/`) producen estos archivos desde un maestro único, con validación previa de RUTs y clientes; montos verificados al peso contra los archivos reales de julio y enero.

### 2.3 Recaudación y cobranza
1. Carga de deuda masiva en Manager+ (devengos mensuales de seguros + cuota social anual).
2. Nóminas PAC/PAT a los bancos para cargo automático (~80% de seguros). **Reintentos automáticos** del ciclo PAC/PAT ante rechazo.
3. **Rechazos de cargo** — causas frecuentes: monto tope de la tarjeta (ej. tope $90.000), problemas de la tarjeta. El estado de convenios y cargos se revisa en el **portal de Transbank** (tesorería/estado de socios y períodos de cargo); los reportes no muestran el número de tarjeta rechazada.
4. **Cambio de tarjeta:** primero se desactiva la tarjeta en la entidad bancaria y recién entonces se inscribe la nueva. Cambio de PAC a cuenta corriente: requiere enviar el documento original a la oficina y puede demorar **hasta 60 días**.
5. Socios de pago directo: correo con monto; pagos por transferencia, depósito y Webpay. Los socios envían **comprobantes por correo a Oriana** (la visualización de pagos puede tardar días); Webpay se verifica por código de comercio contra la cuenta de la Cámara.
6. **Ciclo Addval:** Marcos envía el cierre diario de transacciones (L-V); Addval registra en Manager+ dentro de 48 h y rebaja deuda. No existe aún control formal del cumplimiento del plazo.
7. Se activa "Cuota social al día" en Zoho para socios regularizados (export/actualización de la base, p. ej. corte del 1 de julio).
8. Los mantenedores son la fuente confiable del estado de socios y seguros activos (recomendación de Oriana).

### 2.4 Morosidad y eliminación (ciclo anual real — cuota social)
- Socio **moroso desde mayo**; gestión de cobro (correos, llamadas) entre mayo y julio.
- **1 de julio:** dos envíos de comunicación — (a) socios eliminados por morosidad de cuota social, (b) socios con seguros en morosidad. Plazo de revisión de pagos hasta el día 7; la eliminación formal se ejecuta después de esa revisión.
- **Reincorporación:** el socio que vuelve debe **pagar el año en que se reincorpora** y presentar el comprobante como evidencia.
- Seguros: parámetro de morosidad "9" (☐ precisar unidad/regla con Oriana — ver decisiones).
- Renuncias: correo de confirmación al socio antes de procesar la baja. Beneficiarios y traspasos de cuota entre empresas: Carla.

### 2.5 Conciliación bancaria (mensual, post cierre de mes)
La cartola del Banco de Chile se descarga del portal **en PDF y en Excel** (el TXT no es un formato de cartola: es exclusivamente el archivo de **nómina de pagos** que se carga al banco). El archivo **PRECONCILIACIÓN** se usa para la conciliación mensual que se hace **después del "cierre de mes"**: es la cartola del período enriquecida a mano con columnas RUT/CONCEPTO/MÓDULO/CUENTA/OT/CC/LN y estado por fila. Se cuadra contra la cartola, se importa a Manager+ (conciliación automática por fecha+monto, ~78%) y el resto se concilia a mano (convenios PAC: un documento contra múltiples abonos).

**Puente construido (2026-07-07):** el cruzador de pagos (`herramientas/cruzador-pagos/`) genera el borrador de la PRECONCILIACIÓN desde la cartola + resumen Transbank + maestro, clasificando movimientos y proponiendo RUT.

### 2.6 Puntos críticos del AS-IS (actualizados)
| # | Dolor | Impacto | Estado v2.0 |
|---|---|---|---|
| PC-01 | Cruce de pagos entre 3 fuentes (Manager+, Zoho, Excel), ~10 hrs/sem | Alto | Mitigable con el cruzador (calibración pendiente) |
| PC-02 | ~~Addval sin SLA~~ → ciclo diario existe (48 h) pero **sin control de cumplimiento** | Alto | Reformulado; el cruzador puede producir el control |
| PC-03 | UF manual para cada cobro/incorporación | Medio | Herramienta 04 + generadores lo cubren |
| PC-04 | Separación fondos propios/terceros manual | Crítico | Sin cambio; reporte mensual en el puente, estructural en Odoo |
| PC-05 | Sin métricas de emailings de cobranza | Medio | Sin cambio (Campaigns en Ola 2 del plan puente) |
| PC-06 | Devengos copiando Excel del mes anterior | Alto | **Resuelto en puente** (generadores; mes en paralelo pendiente) |
| PC-07 | Conciliación PAC un-documento↔varios-abonos manual | Alto | Sin cambio (nativo en Odoo) |
| PC-08 | Morosidad sin proceso sistematizado | Alto | Ciclo anual documentado (§2.4); política en borrador para validar |
| PC-09 (nuevo) | Rechazos PAC/PAT sin reporte de causa por socio (número de tarjeta no visible) | Medio | Levantar rendición PAC del banco |

## 3. Diseño futuro en Odoo (TO-BE)

Sin cambios de fondo respecto de v1.0 (contactos + suscripciones + devengo automático + follow-up + conciliación nativa), con estas precisiones:
- Los productos de suscripción se configuran con los valores y cuentas de §1.2 (incluidas las cuentas cruzadas de persona y la UF por fecha específica por seguro). Ver `docs/odoo/Especificacion_Suscripciones_Cobro_Recurrente_Odoo.md`.
- La cuota social empresa se modela con cantidad = unidades UF (3 + adicionales por miembro desde el 4º), recalculada en la renovación anual.
- El registro de pagos se internaliza o se mantiene con Addval con usuario limitado en Odoo, con SLA de 48 h medido por el sistema.
- Las reglas de morosidad parametrizan el ciclo real (§2.4): aging desde el vencimiento, comunicados masivos programados, suspensión/eliminación con ventana de revisión, reincorporación con pago del año en curso.

## 4. Reportes clave
Recaudación por período/producto/cámara · morosidad por tramo y producto (con corte anual de eliminación) · fondos de terceros: recaudado vs pagado a aseguradoras · cumplimiento Addval (envío vs registro, 48 h) · rechazos PAC/PAT y recuperación · efectividad de correos de cobranza · tasa de auto-conciliación.

## 5. Decisiones pendientes (actualizadas)
| # | Decisión | Responsable |
|---|---|---|
| DP-01 | Rol de Addval post-migración (internalizar vs acceso limitado) | Patricio + Constanza |
| DP-02 | Control de cumplimiento del plazo 48 h de Addval (hoy sin registro) | Patricio + Marcos |
| DP-03 | Pasarela PAC/PAT (Toku/Nuvei/otro) | Patricio + Partner |
| DP-04 | Regla de morosidad de seguros ("9": ☐ precisar si son meses, UF u otro) y formalización de la política (borrador en `docs/fase-0/`) | Constanza + Oriana |
| DP-05 | UF de cierre enero/febrero/marzo: precisar cuál aplica a qué caso de cuota social | Patricio |
| DP-06 | Pagos parciales: reglas contables | Patricio |
| DP-07 | Fecha de corte del devengo mensual de seguros | Patricio + Oriana |
| DP-08 | Saldos iniciales Manager+: migración total o corte contable | Patricio + Partner |

---

**Preparado por:** José Ramón Jottar — JR Jottar Consultoría
**Pendiente de validación por:** Oriana Romero (Recaudación) · Patricio Fernández (Adm. y Finanzas) · Marcos Ibarra (Adm. y Control de Gestión)
