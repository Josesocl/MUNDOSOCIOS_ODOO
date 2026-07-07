# Especificación de configuración — Suscripciones y cobro recurrente en Odoo

**Proyecto:** MundoSocios CChC — Implementación Odoo Enterprise
**Alcance:** cuota social y primas de seguros (productos recurrentes tipo suscripción: compromiso anual, cobro mensual o anual según producto)
**Complementa:** `BP_Devengo_Recaudacion_Cobranza_MundoSocios` (v1.0) — este documento baja el TO-BE de ese blueprint a configuración implementable por el partner.
**Fecha:** 2026-07-07 · **Estado:** propuesta para validación (Patricio Fernández / Oriana Romero / partner)

---

## 1. Modelo de productos recurrentes

Cada socio titular mantiene una **membresía anual** (cuota social) y cero o más **seguros** cuya prima se cobra mensualmente. Ambos se modelan como suscripciones en Odoo (`sale.subscription` / planes recurrentes de ventas), con plan de facturación distinto:

| Producto | Plan | Compromiso | Facturación | Precio (verificado 2026) | Cuenta CxC | Cuenta ingreso | Doc. legado |
|---|---|---|---|---|---|---|---|
| Cuota Social Empresa | Membresía | Anual (renovación automática) | **Anual** (devengo único al 1 de enero) | **3 UF hasta 3 miembros + 1 UF por miembro desde el 4º** | 1150001 | 3210002 | CSEMP |
| Cuota Social Persona | Membresía | Anual | **Anual** | **1 UF** | **1150002** | **3210001** | CSPER |
| Seguro Plan Socios | Seguro | Anual (renovación automática) | **Mensual** | factor UF por póliza | 1130004 | 3310005 | PSOC |
| Seguro Complementario | Seguro | Anual | **Mensual** | factor UF · **UF del día 9** | 1130003 | 3310003 | SCOMP |
| Seguro Catastrófico | Seguro | Anual | **Mensual** | factor UF · **UF del último día del mes anterior** | 1130002 | 3310001 | SCAT |
| Plan Carreño | Seguro | Anual | **Mensual** | factor UF (0,2/0,4/0,6) | 1130005 | 3310004 | PCARR |

> Valores y cuentas verificados contra los archivos productivos `DEVENGO * JUL-26 / ENE-26` (2026-07-07). Ojo: las cuentas de cuota social PERSONA van cruzadas respecto de la documentación anterior del proyecto (1150002→3210001); los documentos que digan "0,48/1,44 UF" están desactualizados. La UF del devengo anual de cuota social se toma según regla del cliente (UF de cierre de enero/febrero/marzo — **precisar cuál aplica a qué** con Patricio; el devengo ENE-26 real usó UF $39.731,77).

Decisiones de configuración:
- **Un producto por seguro** con precio variable por línea (factor UF de la póliza en la línea de suscripción), no un producto por tramo. El factor UF vive en la suscripción del socio.
- **La cuota social empresa se configura con cantidad = unidades UF** (3 + adicionales por miembro extra), manteniendo el nº de miembros como campo del contacto que recalcula las unidades en la renovación anual.
- **Cada seguro toma la UF de una fecha distinta** (día 9 / último día del mes anterior): en Odoo esto es una tasa de moneda por fecha específica por producto — configurar la fecha de tasa en la regla de facturación de cada plan, no una UF global.
- **Cuentas contables definidas en el producto** (categoría contable por producto): la separación fondos propios (cuota social) vs fondos de terceros (seguros) queda estructural — nadie la puede "olvidar" (elimina PC-04).
- Si el cliente decide ofrecer **cuota social en 12 pagos**, se agrega una variante del plan Membresía con facturación mensual (1,44/12 UF); el compromiso sigue siendo anual. Registrarlo como decisión DP (ver §8).

## 2. UF: precio y presentación

- Moneda secundaria **CLF (UF)** activada, con tasa actualizada **diariamente** por acción programada (fuente: servicio de indicadores / mindicador.cl / banco central; definir con partner). Elimina PC-03 (UF manual desde la web del SII).
- Los precios de lista se definen **en UF**; la nota de cobro se emite en CLP a la tasa de la fecha de emisión.
- **Restricción conocida (ficha Odoo México, R4):** la interfaz y el portal muestran CLP. Aceptar mostrando en la descripción de línea el detalle "X,XX UF × $UF del día" (plantilla de descripción), o presupuestar desarrollo menor de presentación. Decisión del cliente (§8).

## 3. Ciclo mensual de devengo y cobro (TO-BE operativo)

| Paso | Cuándo | Qué hace el sistema | Reemplaza |
|---|---|---|---|
| 1. Generación | Día 1 de cada mes (cron) | Emite ~1.500 notas de cobro de seguros (+ cuotas sociales que renuevan ese mes) desde las suscripciones activas | Los 4 Excel de devengo copiados a mano + importador |
| 2. Asiento | Automático con cada nota | DEBE CxC / HABER ingreso según producto; diario separado `Seguros (fondos de terceros)` vs `Cuota Social` | Comprobante Traspaso manual / archivo 22 columnas |
| 3. Cobro PAC/PAT | Día 2–5 | Lote de cargos a la pasarela (Toku/Nuvei — **integración, no nativo**); confirmaciones marcan la nota pagada; rechazos disparan correo automático con enlace de pago | Nóminas PAC/PAT armadas a mano + correos manuales |
| 4. Pago directo | Continuo | Webpay/transferencia; el pago entra por el diario del banco y se concilia contra la nota | Registro por Addval con frecuencia errática |
| 5. Seguimiento | Automático | Recordatorio 7d, segundo aviso 15d, escalamiento 30d (Follow-up nativo, ver política de morosidad en `docs/fase-0/`) | No existe hoy (PC-08) |
| 6. Estado del socio | Automático | "Cuota al día" / "Moroso" visible en la ficha del contacto y el portal | Cruce semanal de 3 fuentes por Oriana (PC-01, ~10 h/sem) |

## 4. Diarios y plan de cuentas

- Diario de ventas **"Cuota Social"** (fondos propios) y diario **"Seguros — fondos de terceros"**, cada uno con secuencia propia → los reportes de fondos de terceros salen por filtro de diario, sin planillas.
- Mantener los códigos de cuenta actuales (1150001/3210002; 1130002–5/3310001,3,4,5) en el plan de cuentas Odoo para continuidad con Manager+ y comparabilidad histórica.
- Cuenta analítica por **cámara regional** (dimensión analítica en el contacto/suscripción) para el reporte "estado de cuota social por cámara".

## 5. Datos maestros y migración

| Origen | Destino Odoo | Notas |
|---|---|---|
| Excel Cuota Social 2026 | Contactos (titulares + cargas como contactos hijos) + suscripciones de membresía | ~1.955 titulares, ~2.845 cargas; RUT como identificador; validar DV en la carga |
| Mantenedores Drive (4 seguros) → **maestro único** | Líneas de suscripción de seguros (factor UF, medio de pago) | ~1.500 pólizas. El maestro único ya es el insumo del generador de devengos (`herramientas/generador-devengos/`) — construirlo AHORA sirve al puente y a la migración |
| Manager+ saldos CxC | Asientos de apertura | ~1.500 saldos; definir corte (DP-08) |
| Zoho CRM estado de cuota | Campo de estado en contacto | Se reemplaza por estado calculado desde las notas |

**Regla de oro:** el maestro único de pólizas se construye una sola vez, se usa desde ya para generar los devengos de Manager+ (puente) y llega limpio a la migración. Evita limpiar dos veces.

## 6. Integraciones y desarrollos (con alerta de costo)

| Ítem | Tipo | Criticidad | Alerta |
|---|---|---|---|
| Pasarela PAC/PAT (Toku o Nuvei) | Desarrollo/integración | **Crítica** (80% de primas) | Odoo NO conecta Webpay/PAC/PAT nativo (ficha Odoo MX, R2). Confirmar con el partner qué cubren sus horas ANTES de firmar |
| Motor de emisión masiva | Configuración + desarrollo menor | Crítica | Suscripciones nativas generan las notas; el desarrollo es el empaquetado del lote PAC/PAT y reportería de rechazos |
| Conciliación extracto Banco de Chile | Configuración | Alta | Importación CSV/OFX nativa; pedir al banco cartola en formato importable (hoy PDF) |
| Actualización diaria UF | Configuración | Alta | Acción programada estándar |
| Portal del socio (estado de cuenta, pagar en línea) | Configuración + desarrollo menor | Media | Portal nativo cubre facturas/pagos; personalización de seguros/cargas es desarrollo |

## 7. Reportes y KPIs del ciclo

1. Recaudación por período / producto / cámara.
2. Morosidad por tramo de atraso (7/15/30/60+) y por producto.
3. **Fondos de terceros: recaudado vs pagado a aseguradoras** (por diario) — hoy inexistente y de riesgo crítico.
4. Tasa de auto-conciliación bancaria (meta: ≥ 90%; base actual ~78%).
5. Efectividad de correos de cobro (apertura/clic/conversión) — hoy sin métricas (PC-05).
6. Tasa de rechazo PAC/PAT y recuperación posterior.

## 8. Decisiones que el cliente debe cerrar (bloquean configuración)

| # | Decisión | Recomendación |
|---|---|---|
| S-01 | ¿Cuota social en 1 pago anual (statu quo) o opción de 12 cuotas? | Mantener anual el año 1; evaluar mensual después del go-live |
| S-02 | Pasarela PAC/PAT: ¿Toku o Nuvei? | Pedir a ambos: cobertura PAC+PAT+Webpay, comisiones, conciliación automática con Odoo Chile |
| S-03 | ¿Presentación UF en portal es aceptable en CLP con detalle en la glosa? | Sí para el go-live; desarrollo de presentación después si molesta |
| S-04 | Fecha de corte del devengo mensual (¿día 1?) | Día 1 (DP-07 del BP) |
| S-05 | Morosidad y pagos parciales | Ver borrador de política en `docs/fase-0/Politica_morosidad_y_pagos_parciales_BORRADOR.md` |
| S-06 | Rol de Addval post-migración | Internalizar el registro (Odoo concilia solo); Addval solo si aporta en cobranza telefónica |

---

**Pendiente de validación por:** Patricio Fernández (Adm. y Finanzas) · Oriana Romero (Recaudación) · partner Odoo seleccionado.
