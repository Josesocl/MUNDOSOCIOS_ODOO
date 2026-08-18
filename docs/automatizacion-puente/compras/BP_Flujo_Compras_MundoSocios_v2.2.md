CONFIDENCIAL — MundoSocios CChC · Borrador para revisión

# Blueprint — Flujo de Compras, Cotizaciones y Solicitudes Internas

Insumo para implementación Odoo Enterprise
Proyecto: Implementación Odoo Enterprise — MundoSocios CChC · Fase: Fase 0 — Levantamiento y Diseño
Fuentes: Patricio Fernández (Adm. y Finanzas), Cecilia Ramírez (OC/Compras), manuales operativos
Elaborado por: JR Jottar Consultoría · Versión: **2.2 — 2026-08-18** · Borrador para validación

### Registro de cambios v2.2 (respecto de v2.1)

1.  Matriz de aprobaciones §2.5 corregida según definición de MundoSocios
    (2026-08-18): **en el puente rige la matriz de 4 tramos en CLP con
    aprobadores nominados** (copia PF 2026-07/08); el esquema en UF por
    rol pasa a ser el diseño para **Odoo** (§2.6).
2.  Nueva §2.6: flujo de aprobación para Odoo (láminas PF 2026-08-07 +
    flujos Caso 1/Caso 2), incluida la regla de **aprobación por
    fracción de centro de costo** en gastos multi-partida. Documento
    dedicado: `Flujo_Aprobacion_Compras_Odoo_v1.1.md`.

### Registro de cambios v2.1 (respecto de v2.0, revisada por MundoSocios)

1.  **SimpleAPI reemplaza a API Gateway** como proveedor de servicios SII
    (decisión 2026-07-31; API key contratada, vigente hasta 31-07-2027).
    Es API directa con key: **no requiere token de sesión ni proxy** — el
    proxy Squid de GCP se puede apagar. DP-05 pasa a **Resuelta**.
2.  Matriz de aprobaciones §2.5 **validada por MundoSocios** (revisión
    2026-08): 3 tramos en CLP bruto c/IVA.
3.  Verificación SII del alta de proveedores automatizada con
    `alta_proveedor.py` (`herramientas/sii-simpleapi/` del repo) — ver
    blueprint de proveedores v1.3.

### Registro de cambios v2.0 (respecto de v1.0, julio 2026)

1.  Nueva sección §4: puente en Zoho CRM en construcción con soporte
    oficial (sesión con Alexander Gutiérrez, 2026-07-07) — Sandbox,
    módulo de Proveedores, validación de RUT y SII.
2.  Referencia a las herramientas Fase 0 vigentes (planillas 01/02/03/05)
    como puente hasta Odoo.
3.  Decisión DP-05 actualizada.

------------------------------------------------------------------------

## 1. Contexto del área

El área de Administración y Finanzas gestiona el ciclo completo de
compras: desde la solicitud del área requirente hasta el pago al
proveedor y su conciliación bancaria. Además maneja solicitudes internas
de servicios (sala, alimentación, pasajes, alojamiento) con proveedores
específicos (Aramark, Travel Security, Chicureo Travel, hoteles).

Interlocutores: Patricio Fernández (líder Adm. y Finanzas) · Cecilia
Ramírez (OC/Compras, cramirez@cchc.cl) · Herramientas actuales: Zoho CRM
(formularios y, desde julio 2026, módulo de Proveedores en Sandbox),
Manager+ (OC, facturas, CxP, nóminas, TXT), OneDrive (planillas
paralelas), correo, Banco de Chile.

## 2. Proceso: Flujo de Compras

### 2.1 Situación actual (AS-IS)

Solicitud y cotización: formulario Zoho o correo → verificación (rechazo
si incompleta) → listado de proveedores en Drive/internet → cotización
por correo (2 días de plazo; 3 días para comparar y confirmar; se define
medio de pago: caja chica vs crédito/nómina). Orden de compra: solicitud
de OC a Cecilia Ramírez (c/c Patricio) → OC en Manager+ → envío al
proveedor → registro en Drive ("Detalle de Solicitud de Cotizaciones
24"). Factura, pago y cierre: factura asociada a la OC en Manager+ → CxP
→ recepción conforme → nómina de los martes → TXT Banco de Chile (cta.
8001104309) → inscripción por Patricio + aprobación de apoderados →
abono → conciliación → cierre del caso en Zoho con respaldos.

### 2.2 Puntos críticos

- Fragmentación en 5 sistemas sin integración; doble/triple registro
  (Zoho → Drive → Manager+).
- TXT frágil: campos vacíos del maestro, caracteres especiales,
  descripción >400, **fecha de pago editada a mano**.
- Dependencia de personas: Cecilia (única creadora de OC), Patricio
  (único inscriptor en banco).
- Aprobaciones por correo sin registro sistemático; respaldo documental
  disperso.

### 2.3 Puente vigente (hasta Odoo)

Las herramientas de `Fase 0/` + `Herramientas Operativas/` cubren el
control sin Zoho Blueprint: `01_Ficha_Proveedor` (semáforo APTO),
`02_Registro_y_Plantilla_OC` (IVA, total y tramo de aprobación
automáticos + registro de quién aprobó), `03_Control_Nomina_Pago`
(validaciones del TXT + cruce bancario por RUT),
`05_Conciliacion_Bancaria`. Desde 2026-08 se suma
**`alta_proveedor.py`** (verificación SII automática con registro
fechado). Regla de avance: ningún proveedor entra a OC o nómina sin
estado APTO.

### 2.4 Flujo optimizado en Odoo (TO-BE)

Sin cambios respecto de v1.0: solicitud → validación → RFQ → selección y
OC → aprobación paramétrica → envío → factura asociada (match RUT+OC) →
CxP → recepción → expediente documental → lote de pago → TXT Banco de
Chile (desarrollo; requiere Odoo.sh) → carga y aprobación bancaria →
pago y conciliación.

### 2.5 Matriz de aprobaciones VIGENTE en el puente (CLP bruto c/IVA) — definición MundoSocios 2026-08-18

Rige hasta la salida en Odoo (aprobadores nominados, copia PF 2026-07/08):

| Tramo | Aprobador |
|---|---|
| Hasta $500.000 | Dueño del presupuesto (por centro de costo) |
| $500.001 – $1.000.000 | Cecilia Ramírez |
| $1.000.001 – $5.000.000 | Patricio Fernández |
| > $5.000.000 | Patricio Fernández + Constanza Daniels (Gerente General) |

En Odoo esta matriz **cambia** al esquema paramétrico en UF por rol (§2.6);
los bordes calzan: 13 UF ≈ $531.000 y 125 UF ≈ $5.100.000.

### 2.6 Flujo de aprobación para Odoo (TO-BE, en UF) — láminas PF 2026-08-07

Definido en los flujos Caso 1 (con OC) y Caso 2 (factura directa) —
detalle y diagramas en `Flujo_Aprobacion_Compras_Odoo_v1.1.md`:

- **Umbral de cotización:** compras ≥ **13 UF** exigen 2 cotizaciones
  adjuntas; bajo eso, sin cotizaciones.
- **Presupuesto bloqueante:** sin saldo presupuestario la compra se
  detiene; solo el Gerente puede aprobar la excepción
  (ampliación/reasignación). Sin excepción: solicitud cancelada (Caso 1)
  o rechazo del DTE en el SII / devolución al proveedor (Caso 2, dentro
  de la ventana legal de 8 días).
- **Nivel de aprobación:** ≤ **125 UF** aprueba el Líder responsable;
  > 125 UF aprueban Líder responsable + Gerente General (secuencial).
- **Multi-partida:** si el gasto se divide en varias cuentas/centros de
  costo, **cada Líder de CC aprueba su fracción** para liberar el flujo.
- **Validación contable** (Caso 1): coincidencia OC/recepción, cuenta y
  CC correctos; si falla, la factura queda **retenida** y vuelve a
  validación tras corregir la imputación (nunca directo a pago).

## 3. Subprocesos

Cotizaciones (TO-BE): RFQ desde la solicitud, respuestas en Odoo (portal
o correo), comparación consolidada, conversión a OC; se eliminan Drive,
correo de aprobaciones y cierre manual en Zoho. Solicitudes internas
(sala/alimentación/pasajes/alojamiento): tipo específico dentro de
Compras o Helpdesk interno, con formularios condicionados por tipo y
catálogo Aramark precargado; misma matriz de aprobación. Creación de
clientes/proveedores: ver blueprint dedicado
(`BP_Proceso_Creacion_Proveedor_MundoSocios_v1.3.md`) — maestro
unificado en Contactos con validaciones bloqueantes de RUT y datos
bancarios; migración desde Manager+ con los campos mapeados (RUT, razón
social, giro, correo SII, dirección, cuenta bancaria).

## 4. Puente en Zoho CRM — avances con soporte oficial (2026-07-07) *(actualizado en v2.1)*

Sesión técnica con **Alexander Gutiérrez** (soporte Zoho). El descarte
de la capa Zoho autoconstruida (2026-07-06) se mantiene; lo que cambia
es que **el soporte oficial de Zoho construye** las piezas de
proveedores/validación, usando el diseño de referencia y el Validador
SII como especificación.

Decisiones tomadas:

- Sandbox habilitado con datos de productivo, en espacio aislado; envío
  de correos deshabilitado por defecto (evita envíos accidentales).
- Módulo de Proveedores activado en Zoho CRM (estaba deshabilitado).
  Campos clave definidos: RUT, razón social, nombre de fantasía, giro,
  representante legal, contacto comercial.
- Validación del RUT como regla de validación del módulo, con función
  personalizada (no criterios simples).
- **Integración SII vía SimpleAPI** *(actualizado: en la sesión se
  habló de API Gateway; el 2026-07-31 se contrató SimpleAPI en su
  reemplazo)*: `GET https://rut.simpleapi.cl/v2/{rut}`, header
  `Authorization` con la API key directa. **Sin token de sesión y sin
  proxy** — los pendientes de token/proxy de la sesión quedaron
  obsoletos; el proxy Squid de GCP se puede apagar. Especificación
  completa (endpoint, esquema de respuesta y mapeo de campos) en
  `herramientas/sii-simpleapi/README.md` del repo — enviar ese README a
  Alexander.
- Resincronización de correos post-migración Google→Microsoft:
  Alexander envía el paso a paso.

Ítems de acción: Alexander crea el módulo de Proveedores al recibir la
planilla de campos · el consultor/Patricio envían la planilla de campos
y la documentación de automatizaciones · Patricio gestiona ticket a TI
por el error de autorización de Outlook · el consultor envía a Alexander
el README de SimpleAPI y `alta_proveedor.py` como referencia de
comportamiento (reemplaza el envío del Validador SII legado).

Pendientes/preguntas abiertas: ¿el Sandbox permite habilitar correo
hacia una cuenta específica para probar aprobaciones? · ¿la validación
tributaria corre al crear el registro o como automatización posterior? ·
¿proveedores como módulo separado o como tipo de cuenta dentro de
Socios?

## 5. Integraciones y desarrollos requeridos (Odoo)

| Ítem | Tipo | Prioridad | Nota |
|---|---|---|---|
| TXT Banco de Chile | Desarrollo | Crítica | No nativo; requiere Odoo.sh; formato cta. 8001104309 |
| Match factura ↔ OC | Configuración | Alta | Nativo (RUT + ref. OC) |
| Aprobaciones paramétricas | Configuración | Alta | Nativo en Purchase por orden completa (esquema UF §2.6); la aprobación por fracción de CC (multi-partida) NO es nativa — requiere Studio/desarrollo |
| Conciliación bancaria | Configuración | Alta | Nativo; importación de extracto |
| Portal del proveedor | Estándar | Media | Cotizaciones por portal |
| Validación SII | Integración | Alta | **Resuelta en el puente vía SimpleAPI** (cliente + alta_proveedor operativos); en Odoo se replica con el mismo servicio |

## 6. Decisiones pendientes (actualizadas)

| # | Decisión | Responsable | Estado |
|---|---|---|---|
| DP-01 | Hosting: Odoo.sh (requerido para TXT) vs Online | Constanza + Patricio | Abierta |
| DP-02 | Solicitudes internas: Compras vs Helpdesk | JR + Partner | Abierta |
| DP-03 | Formularios: Studio vs desarrollo | Partner | Abierta |
| DP-04 | Caja chica: dentro o fuera de Odoo | Patricio | Abierta (entrevista B1) |
| DP-05 | Validación SII | Patricio + Partner | **Resuelta**: SimpleAPI contratada (2026-07-31, key vigente hasta 31-07-2027); cliente y alta de proveedor operativos en `herramientas/sii-simpleapi/` |
| DP-06 | Portal del proveedor | Cecilia | Abierta |
| DP-07 | Catálogo Aramark como productos | Cecilia + Partner | Abierta |
| DP-08 | Validación del TXT en Odoo antes de cargar al banco | Patricio | Abierta |
| DP-09 | Proveedores en Zoho: módulo separado vs tipo de cuenta en Socios | Patricio + Alexander | Abierta |

------------------------------------------------------------------------

Preparado por: José Ramón Jottar — JR Jottar Consultoría
Pendiente de validación por: Patricio Fernández (Adm. y Finanzas) · Cecilia Ramírez (OC/Compras)
