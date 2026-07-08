# Blueprint — Proceso de Creación de Proveedor

**Proyecto:** Implementación Odoo Enterprise — MundoSocios CChC
**Fase:** Fase 0 — Levantamiento y diseño · **Versión:** 1.2 · **Fecha:** 2026-07-08
**Fuentes:** Manual creación de proveedores (transcrito), Checklist campos críticos del proveedor v2.0 (Fase 0), Manual nóminas de pago, ficha `01_Ficha_Proveedor_MundoSocios.xlsx`, sesión técnica con soporte Zoho (Alexander Gutiérrez, 2026-07-07).

> **v1.2:** se agrega §3b — el puente de proveedores ahora se construye también en Zoho CRM con soporte oficial (módulo de Proveedores + validación RUT + SII vía API Gateway).

> **Nota:** este documento reemplaza a `BP_Proceso_Creación_Proveedor_MundoSocios.docx`, cuyo contenido quedó duplicado por error con el blueprint de Experiencia/Atención. Al copiarlo a OneDrive, eliminar o marcar como obsoleto el .docx defectuoso.

---

## 1. Contexto

La calidad del maestro de proveedores es la causa raíz #1 de fallas del TXT bancario (dolor #1 del diagnóstico): un campo vacío o mal digitado en el proveedor rompe la carga de la nómina en el Banco de Chile el día de pago. Este proceso es previo y habilitante para compras (OC), ingreso de facturas y nóminas.

**Actores:** Cecilia Ramírez (compras/OC), encargado de tesorería, Patricio Fernández (supervisión). Volumen: bajo (altas puntuales), impacto: alto.

## 2. Situación actual (AS-IS)

1. Verificar situación tributaria del RUT en `zeus.sii.cl` (Consultar situación tributaria de terceros): inicio de actividades, actividades vigentes, afectación IVA. Copiar RUT + razón social + giro desde el SII (recomendación del manual: copy-paste para evitar errores de tipeo).
2. Manager+ > Mantenedores > Clientes y/o proveedores > Crear cliente/proveedor.
3. Completar campos mínimos: RUT, razón social, nombre de fantasía (o repetir razón social), giro, clasificación "sin clasificación", correo SII, correo comercial, **tipo proveedor: Nacional (facturas) u Honorario (boletas)**, plazo de pago 30 días, dirección completa (descripción, dirección, comuna, ciudad, región, país).
4. Pestaña **Contactos**: nombre, cargo, correo, teléfono y **saludo (Estimado/Estimada)** — Manager+ lo usa en el envío automático de la OC.
5. Pestaña **Cuentas bancarias**: tipo de cuenta, número, banco, cuenta por defecto.

### Puntos críticos del AS-IS

| # | Dolor | Impacto |
|---|---|---|
| PC-P1 | Los campos marcados en rojo sin información **generan error en el TXT y la nómina no se puede cargar en banco** — la validación es solo una advertencia del manual, el sistema no obliga | Crítico |
| PC-P2 | Consulta SII manual (web con captcha), copy-paste; sin registro de la verificación | Alto |
| PC-P3 | Los datos bancarios no se re-verifican al momento de pagar (requerimiento RF-06b) | Alto |
| PC-P4 | Sin dueño formal del alta ni segregación alta/pago | Medio |
| PC-P5 | Maestro con proveedores incompletos históricos que fallan al primer pago | Alto |

## 3. Proceso puente vigente (con las herramientas Fase 0)

1. **`01_Ficha_Proveedor_MundoSocios.xlsx`**: registrar el alta con el checklist de campos críticos v2.0; el semáforo **APTO / EN VALIDACIÓN** bloquea el uso del proveedor en OC hasta completar todo.
2. **Validador SII** (CLI/servidor local): valida RUT (módulo 11) y situación tributaria; deja registro HTML de la verificación (reemplaza PC-P2 cuando se contrate API Gateway; mientras tanto, modo manual-asistido).
3. Crear en Manager+ **solo** proveedores APTO, copiando desde la ficha (una sola digitación fuente).
4. En la nómina (`03_Control_Nomina_Pago_MundoSocios.xlsx`), el cruce por RUT contra la hoja Proveedores alerta discrepancias de banco/cuenta/estado **antes** de emitir el TXT (cubre RF-06b de forma interina).

**Regla de avance:** ningún proveedor entra a una OC ni a una nómina sin estado APTO en la ficha.

## 3b. Puente en Zoho CRM con soporte oficial (2026-07-07) *(nuevo en v1.2)*

En sesión técnica con **Alexander Gutiérrez** (soporte Zoho) se acordó que el soporte oficial construye la capa de proveedores en Zoho, usando el Sandbox y tomando el Validador SII y el checklist v2.0 como especificación:

- **Sandbox** habilitado con datos de productivo (aislado; envío de correos deshabilitado por defecto).
- **Módulo de Proveedores activado** en Zoho CRM. Campos clave definidos: RUT, razón social, nombre de fantasía, giro, representante legal, contacto comercial (alineados con el checklist v2.0; falta enviar la planilla completa de campos).
- **Validación del RUT** como regla de validación del módulo con **función personalizada** (módulo 11), no criterios simples.
- **Verificación SII vía API Gateway** (mismo servicio del Validador): pendientes el token y la definición del proxy/alojamiento (el proxy Squid de referencia ya está desplegado en GCP).
- El **Validador SII** (código) se envía a Alexander como referencia de comportamiento.

**Pendientes de esta vía:** ¿proveedores como módulo separado o tipo de cuenta dentro de Socios? · ¿la validación SII corre al crear el registro o como automatización posterior? · habilitación de correos de prueba en Sandbox · token API Gateway (~$10.000 CLP/mes, decisión de Patricio).

Cuando este módulo entre a productivo, reemplaza la ficha Excel `01_Ficha_Proveedor` como punto de alta (la regla APTO se mantiene: la valida Zoho en vez de la planilla); Manager+ sigue recibiendo el alta por digitación/exportación hasta Odoo.

## 4. Diseño futuro en Odoo (TO-BE)

| Etapa | Proceso en Odoo | Módulo |
|---|---|---|
| 1. Alta | Contacto tipo proveedor con **campos obligatorios forzados**: RUT (validado con módulo 11 — localización chilena), razón social, giro, correo, dirección, tipo (Nacional/Honorario vía posición fiscal), plazo de pago | Contactos + l10n_cl |
| 2. Verificación SII | Consulta de situación tributaria al crear (integración API SII de terceros — el Validador actual es la especificación de comportamiento) con registro en el chatter | Desarrollo menor |
| 3. Datos bancarios | Cuenta bancaria obligatoria para proveedores pagables; validación de formato; **re-verificación visible al registrar el pago (RF-06b)** | Contabilidad |
| 4. Aprobación del alta | Actividad de aprobación a Adm. y Finanzas antes de habilitar para compras (segregación alta/pago) | Contactos + actividades |
| 5. Uso | La OC y la factura solo aceptan proveedores completos; el lote de pago valida datos bancarios antes de generar el TXT (desarrollo TXT Banco de Chile — requiere Odoo.sh, ver R1 ficha Odoo MX) | Compras + Contabilidad |

**Requerimientos cubiertos:** RF-04, RF-05, RF-06, RF-06b del Entregable 3.

## 5. Migración del maestro

- Exportar proveedores de Manager+ → pasar por el checklist v2.0 (script o ficha) → **solo migran a Odoo los APTO**; el resto se completa o se archiva.
- No migrar proveedores sin movimiento en 24 meses (proponer; confirmar con Patricio).

## 6. Decisiones pendientes

| # | Decisión | Responsable |
|---|---|---|
| DP-P1 | ¿Quién es el dueño formal del alta de proveedores (¿Cecilia?) y quién aprueba (¿Patricio?)? | Patricio |
| DP-P2 | Contratación API Gateway para verificación SII automática (~$10.000 CLP/mes) | Patricio |
| DP-P3 | Criterio de archivo de proveedores históricos incompletos | Patricio |

---

**Pendiente de validación por:** Patricio Fernández (Adm. y Finanzas) · Cecilia Ramírez (Compras).
