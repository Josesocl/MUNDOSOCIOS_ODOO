CONFIDENCIAL — MundoSocios CChC · Borrador para revisión

# Blueprint — Proceso de Creación de Proveedor

**Proyecto:** Implementación Odoo Enterprise — MundoSocios CChC
**Fase:** Fase 0 — Levantamiento y diseño · **Versión:** 1.3 ·
**Fecha:** 2026-08-14
**Fuentes:** Manual creación de proveedores (transcrito), Checklist
campos críticos del proveedor v2.0 (Fase 0), Manual nóminas de pago,
ficha `01_Ficha_Proveedor_MundoSocios.xlsx`, sesión técnica con soporte
Zoho (Alexander Gutiérrez, 2026-07-07).

> **v1.3 (2026-08-14):** **SimpleAPI reemplaza a API Gateway** en todo
> el documento (decisión 2026-07-31; key contratada hasta 31-07-2027;
> API directa sin token ni proxy). DP-P2 pasa a **Resuelta**. Se
> incorpora la herramienta **`alta_proveedor.py`**
> (`herramientas/sii-simpleapi/` del repo), que automatiza la
> verificación SII del alta con registro fechado — resuelve PC-P2.
>
> **v1.2:** se agrega §3b — el puente de proveedores ahora se construye
> también en Zoho CRM con soporte oficial (módulo de Proveedores +
> validación RUT + SII).
>
> **Nota:** este documento reemplaza a
> `BP_Proceso_Creación_Proveedor_MundoSocios.docx`, cuyo contenido quedó
> duplicado por error con el blueprint de Experiencia/Atención. Al
> copiarlo a OneDrive, eliminar o marcar como obsoleto el .docx
> defectuoso.

------------------------------------------------------------------------

## 1. Contexto

La calidad del maestro de proveedores es la causa raíz #1 de fallas del
TXT bancario (dolor #1 del diagnóstico): un campo vacío o mal digitado
en el proveedor rompe la carga de la nómina en el Banco de Chile el día
de pago. Este proceso es previo y habilitante para compras (OC), ingreso
de facturas y nóminas.

**Actores:** Cecilia Ramírez (compras/OC), encargado de tesorería,
Patricio Fernández (supervisión). Volumen: bajo (altas puntuales),
impacto: alto.

## 2. Situación actual (AS-IS)

1.  Verificar situación tributaria del RUT en `zeus.sii.cl` (Consultar
    situación tributaria de terceros): inicio de actividades,
    actividades vigentes, afectación IVA. Copiar RUT + razón social +
    giro desde el SII (recomendación del manual: copy-paste para evitar
    errores de tipeo).
2.  Manager+ > Mantenedores > Clientes y/o proveedores > Crear
    cliente/proveedor.
3.  Completar campos mínimos: RUT, razón social, nombre de fantasía (o
    repetir razón social), giro, clasificación "sin clasificación",
    correo SII, correo comercial, **tipo proveedor: Nacional (facturas)
    u Honorario (boletas)**, plazo de pago 30 días, dirección completa
    (descripción, dirección, comuna, ciudad, región, país).
4.  Pestaña **Contactos**: nombre, cargo, correo, teléfono y **saludo
    (Estimado/Estimada)** — Manager+ lo usa en el envío automático de
    la OC.
5.  Pestaña **Cuentas bancarias**: tipo de cuenta, número, banco, cuenta
    por defecto.

### Puntos críticos del AS-IS

| # | Dolor | Impacto |
|---|---|---|
| PC-P1 | Los campos marcados en rojo sin información **generan error en el TXT y la nómina no se puede cargar en banco** — la validación es solo una advertencia del manual, el sistema no obliga | Crítico |
| PC-P2 | Consulta SII manual (web con captcha), copy-paste; sin registro de la verificación — **RESUELTO con `alta_proveedor.py` (SimpleAPI + registro fechado HTML/CSV)** | Alto |
| PC-P3 | Los datos bancarios no se re-verifican al momento de pagar (requerimiento RF-06b) | Alto |
| PC-P4 | Sin dueño formal del alta ni segregación alta/pago | Medio |
| PC-P5 | Maestro con proveedores incompletos históricos que fallan al primer pago | Alto |

## 3. Proceso puente vigente (con las herramientas Fase 0) *(actualizado en v1.3)*

1.  **`alta_proveedor.py`** (`herramientas/sii-simpleapi/`): verifica la
    situación tributaria del RUT vía **SimpleAPI** (sin captcha, sin
    copy-paste) y deja **registro fechado** de la verificación — HTML
    por proveedor + bitácora `registro_verificaciones.csv` en
    `verificaciones/` (resuelve PC-P2). Aplica el semáforo del checklist
    v2.0: sin inicio de actividades = **NO APTO** (no se crea). Entrega
    el bloque de campos listo para digitar en Manager+ y sugiere el tipo
    (Nacional/Honorario) según afectación IVA. Caché 90 días y control
    de cuota (10 consultas/mes); repetir un RUT no gasta cuota.
2.  `01_Ficha_Proveedor_MundoSocios.xlsx`: registrar el alta con el
    checklist de campos críticos v2.0 (datos bancarios y contacto); el
    semáforo **APTO / EN VALIDACIÓN** bloquea el uso del proveedor en OC
    hasta completar todo.
3.  Crear en Manager+ **solo** proveedores APTO, copiando desde la
    salida de `alta_proveedor.py` y la ficha (una sola digitación
    fuente).
4.  En la nómina (`03_Control_Nomina_Pago_MundoSocios.xlsx`), el cruce
    por RUT contra la hoja Proveedores alerta discrepancias de
    banco/cuenta/estado **antes** de emitir el TXT (cubre RF-06b de
    forma interina).

**Regla de avance:** ningún proveedor entra a una OC ni a una nómina sin
estado APTO (verificación SII con registro + ficha completa).

## 3b. Puente en Zoho CRM con soporte oficial (2026-07-07) *(actualizado en v1.3)*

En sesión técnica con **Alexander Gutiérrez** (soporte Zoho) se acordó
que el soporte oficial construye la capa de proveedores en Zoho, usando
el Sandbox y tomando el checklist v2.0 como especificación:

- **Sandbox** habilitado con datos de productivo (aislado; envío de
  correos deshabilitado por defecto).
- **Módulo de Proveedores activado** en Zoho CRM. Campos clave
  definidos: RUT, razón social, nombre de fantasía, giro, representante
  legal, contacto comercial (alineados con el checklist v2.0; falta
  enviar la planilla completa de campos).
- **Validación del RUT** como regla de validación del módulo con
  **función personalizada** (módulo 11), no criterios simples.
- **Verificación SII vía SimpleAPI** *(actualizado: en la sesión se
  habló de API Gateway; el 2026-07-31 se contrató SimpleAPI en su
  reemplazo)*: `GET https://rut.simpleapi.cl/v2/{rut}`, header
  `Authorization` con la key directa. **Sin token de sesión y sin
  proxy** — el proxy Squid de GCP quedó obsoleto y se puede apagar.
  Especificación (endpoint, esquema de respuesta, mapeo al checklist) en
  `herramientas/sii-simpleapi/README.md`.
- A Alexander se le envían como referencia de comportamiento el README
  de SimpleAPI y `alta_proveedor.py` (reemplazan al Validador SII
  legado).

**Pendientes de esta vía:** ¿proveedores como módulo separado o tipo de
cuenta dentro de Socios? · ¿la validación SII corre al crear el registro
o como automatización posterior? · habilitación de correos de prueba en
Sandbox. *(El pendiente de token/proxy de API Gateway quedó resuelto con
SimpleAPI.)*

Cuando este módulo entre a productivo, reemplaza la ficha Excel
`01_Ficha_Proveedor` como punto de alta (la regla APTO se mantiene: la
valida Zoho en vez de la planilla); Manager+ sigue recibiendo el alta
por digitación/exportación hasta Odoo.

## 4. Diseño futuro en Odoo (TO-BE)

| Etapa | Proceso en Odoo | Módulo |
|---|---|---|
| 1. Alta | Contacto tipo proveedor con **campos obligatorios forzados**: RUT (validado con módulo 11 — localización chilena), razón social, giro, correo, dirección, tipo (Nacional/Honorario vía posición fiscal), plazo de pago | Contactos + l10n_cl |
| 2. Verificación SII | Consulta de situación tributaria al crear (**integración SimpleAPI** — `alta_proveedor.py` es la especificación de comportamiento) con registro en el chatter | Desarrollo menor |
| 3. Datos bancarios | Cuenta bancaria obligatoria para proveedores pagables; validación de formato; **re-verificación visible al registrar el pago (RF-06b)** | Contabilidad |
| 4. Aprobación del alta | Actividad de aprobación a Adm. y Finanzas antes de habilitar para compras (segregación alta/pago) | Contactos + actividades |
| 5. Uso | La OC y la factura solo aceptan proveedores completos; el lote de pago valida datos bancarios antes de generar el TXT (desarrollo TXT Banco de Chile — requiere Odoo.sh, ver R1 ficha Odoo MX) | Compras + Contabilidad |

**Requerimientos cubiertos:** RF-04, RF-05, RF-06, RF-06b del Entregable 3.

## 5. Migración del maestro

- Exportar proveedores de Manager+ → pasar por el checklist v2.0 (script
  o ficha) → **solo migran a Odoo los APTO**; el resto se completa o se
  archiva.
- *(El criterio adicional de no migrar proveedores sin movimiento en 24
  meses fue retirado en la revisión de MundoSocios; el criterio de
  archivo de históricos queda en DP-P3.)*

## 6. Decisiones pendientes

| # | Decisión | Responsable | Estado |
|---|---|---|---|
| DP-P1 | ¿Quién es el dueño formal del alta de proveedores (¿Cecilia?) y quién aprueba (¿Patricio?)? | Patricio | Abierta |
| DP-P2 | Contratación de servicio para verificación SII automática | Patricio | **Resuelta**: SimpleAPI contratada (2026-07-31, key vigente hasta 31-07-2027); `alta_proveedor.py` operativo |
| DP-P3 | Criterio de archivo de proveedores históricos incompletos | Patricio | Abierta |

------------------------------------------------------------------------

**Pendiente de validación por:** Patricio Fernández (Adm. y Finanzas) ·
Cecilia Ramírez (Compras).
