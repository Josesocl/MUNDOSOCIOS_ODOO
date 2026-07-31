# Blueprint — Flujo de Compras, Cotizaciones y Solicitudes Internas

**Insumo para implementación Odoo Enterprise**
**Proyecto:** Implementación Odoo Enterprise — MundoSocios CChC · **Fase:** Fase 0 — Levantamiento y Diseño
**Fuentes:** Patricio Fernández (Adm. y Finanzas), Cecilia Ramírez (OC/Compras), manuales operativos
**Elaborado por:** JR Jottar Consultoría · **Versión:** 2.0 — 2026-07-08 · Borrador para validación

### Registro de cambios v2.0 (respecto de v1.0, julio 2026)
1. Nueva sección §4: **puente en Zoho CRM en construcción con soporte oficial** (sesión con Alexander Gutiérrez, 2026-07-07) — Sandbox, módulo de Proveedores, validación de RUT y SII vía API Gateway.
2. Referencia a las herramientas Fase 0 vigentes (planillas 01/02/03/05) como puente hasta Odoo.
3. Decisión DP-05 actualizada (la validación SII ya está en curso vía Zoho + API Gateway, no queda para Fase 2).

---

## 1. Contexto del área
El área de Administración y Finanzas gestiona el ciclo completo de compras: desde la solicitud del área requirente hasta el pago al proveedor y su conciliación bancaria. Además maneja solicitudes internas de servicios (sala, alimentación, pasajes, alojamiento) con proveedores específicos (Aramark, Travel Security, Chicureo Travel, hoteles).

**Interlocutores:** Patricio Fernández (líder Adm. y Finanzas) · Cecilia Ramírez (OC/Compras, cramirez@cchc.cl) · Teresa Fernández (Secretaría piso -1) · Aramark (Daniela Fernández, Marilyn Ale).
**Herramientas actuales:** Zoho CRM (formularios y, desde julio 2026, módulo de Proveedores en Sandbox), Manager+ (OC, facturas, CxP, nóminas, TXT), Google Drive (planillas paralelas), correo, Banco de Chile.

## 2. Proceso: Flujo de Compras

### 2.1 Situación actual (AS-IS)
**Solicitud y cotización:** formulario Zoho o correo → verificación (rechazo si incompleta) → listado de proveedores en Drive/internet → cotización por correo (2 días de plazo; 3 días para comparar y confirmar; se define medio de pago: caja chica vs crédito/nómina).
**Orden de compra:** solicitud de OC a Cecilia Ramírez (c/c Patricio) → OC en Manager+ → envío al proveedor → registro en Drive ("Detalle de Solicitud de Cotizaciones 24").
**Factura, pago y cierre:** factura asociada a la OC en Manager+ → CxP → recepción conforme → nómina de los martes → TXT Banco de Chile (cta. 8001104309) → inscripción por Patricio + aprobación de apoderados → abono → conciliación → cierre del caso en Zoho con respaldos.

### 2.2 Puntos críticos
- Fragmentación en 5 sistemas sin integración; doble/triple registro (Zoho → Drive → Manager+).
- TXT frágil: campos vacíos del maestro, caracteres especiales, descripción >400, **fecha de pago editada a mano**.
- Dependencia de personas: Cecilia (única creadora de OC), Patricio (único inscriptor en banco).
- Aprobaciones por correo sin registro sistemático; respaldo documental disperso.

### 2.3 Puente vigente (hasta Odoo)
Las herramientas de `Fase 0/` + `Herramientas Operativas/` cubren el control sin Zoho Blueprint: `01_Ficha_Proveedor` (semáforo APTO), `02_Registro_y_Plantilla_OC` (IVA, total y tramo de aprobación automáticos + registro de quién aprobó), `03_Control_Nomina_Pago` (validaciones del TXT + cruce bancario por RUT), `05_Conciliacion_Bancaria`. Regla de avance: ningún proveedor entra a OC o nómina sin estado APTO.

### 2.4 Flujo optimizado en Odoo (TO-BE)
Sin cambios respecto de v1.0: solicitud → validación → RFQ → selección y OC → aprobación paramétrica → envío → factura asociada (match RUT+OC) → CxP → recepción → expediente documental → lote de pago → TXT Banco de Chile (desarrollo; requiere Odoo.sh) → carga y aprobación bancaria → pago y conciliación.

### 2.5 Matriz de aprobaciones (paramétrica, CLP bruto c/IVA)
| Tramo | Aprobador | Configuración Odoo |
|---|---|---|
| Hasta $500.000 | Dueño del presupuesto (por CC) | Automática si el solicitante es el dueño del CC |
| $500.001 – $1.000.000 | Cecilia Ramírez | 1 nivel |
| $1.000.001 – $5.000.000 | Patricio Fernández | 1 nivel |
| > $5.000.000 | Patricio Fernández + Constanza Daniels | 2 niveles secuenciales |

## 3. Subprocesos
**Cotizaciones (TO-BE):** RFQ desde la solicitud, respuestas en Odoo (portal o correo), comparación consolidada, conversión a OC; se eliminan Drive, correo de aprobaciones y cierre manual en Zoho.
**Solicitudes internas (sala/alimentación/pasajes/alojamiento):** tipo específico dentro de Compras o Helpdesk interno, con formularios condicionados por tipo y catálogo Aramark precargado; misma matriz de aprobación.
**Creación de clientes/proveedores:** ver blueprint dedicado (`BP_Proceso_Creacion_Proveedor.md`) — maestro unificado en Contactos con validaciones bloqueantes de RUT y datos bancarios; migración desde Manager+ con los campos mapeados (RUT, razón social, giro, correo SII, dirección, cuenta bancaria).

## 4. Puente en Zoho CRM — avances con soporte oficial (2026-07-07) *(nuevo en v2.0)*

Sesión técnica con **Alexander Gutiérrez** (soporte Zoho). El descarte de la capa Zoho autoconstruida (2026-07-06) se mantiene; lo que cambia es que **el soporte oficial de Zoho construye** las piezas de proveedores/validación, usando el diseño de referencia y el Validador SII como especificación.

**Decisiones tomadas:**
- **Sandbox habilitado** con datos de productivo, en espacio aislado; envío de correos deshabilitado por defecto (evita envíos accidentales).
- **Módulo de Proveedores activado** en Zoho CRM (estaba deshabilitado). Campos clave definidos: RUT, razón social, nombre de fantasía, giro, representante legal, contacto comercial.
- **Validación del RUT** como regla de validación del módulo, con **función personalizada** (no criterios simples).
- **Integración SII** — en la sesión se acordó API Gateway; **actualización 2026-07-31: el proveedor definitivo es SimpleAPI (simpleapi.cl)**, con API key contratada vigente hasta 31-07-2027 (sin proxy ni token adicional). Informar a Alexander para que la función personalizada apunte a SimpleAPI (ver `herramientas/sii-simpleapi/`).
- Resincronización de correos post-migración Google→Microsoft: Alexander envía el paso a paso.

**Ítems de acción:** Alexander crea el módulo de Proveedores al recibir la planilla de campos · revisa documentación de API Gateway y el proxy · el consultor/Patricio envían la planilla de campos y la documentación de automatizaciones · Patricio gestiona ticket a TI por el error de autorización de Outlook · el consultor envía el **Validador SII** (código) a Alexander como referencia.

**Pendientes/preguntas abiertas:** ¿el Sandbox permite habilitar correo hacia una cuenta específica para probar aprobaciones? · ¿API Gateway requiere proxy propio (Squid, ya desplegado en GCP como referencia) o tiene servicio listo? · ¿la validación tributaria corre al crear el registro o como automatización posterior? · ¿proveedores como módulo separado o como tipo de cuenta dentro de Socios?

## 5. Integraciones y desarrollos requeridos (Odoo)
| Ítem | Tipo | Prioridad | Nota |
|---|---|---|---|
| TXT Banco de Chile | Desarrollo | Crítica | No nativo; requiere Odoo.sh; formato cta. 8001104309 |
| Match factura ↔ OC | Configuración | Alta | Nativo (RUT + ref. OC) |
| Aprobaciones paramétricas | Configuración | Alta | Nativo en Purchase |
| Conciliación bancaria | Configuración | Alta | Nativo; importación de extracto |
| Portal del proveedor | Estándar | Media | Cotizaciones por portal |
| Validación SII | Integración | Alta *(subida desde Media/Fase 2)* | **En curso en el puente** vía Zoho + API Gateway; en Odoo se replica con el mismo servicio |

## 6. Decisiones pendientes (actualizadas)
| # | Decisión | Responsable | Estado |
|---|---|---|---|
| DP-01 | Hosting: Odoo.sh (requerido para TXT) vs Online | Constanza + Patricio | Abierta |
| DP-02 | Solicitudes internas: Compras vs Helpdesk | JR + Partner | Abierta |
| DP-03 | Formularios: Studio vs desarrollo | Partner | Abierta |
| DP-04 | Caja chica: dentro o fuera de Odoo | Patricio | Abierta (entrevista B1) |
| DP-05 | Validación SII | Patricio + Partner | **Resuelta (2026-07-31)**: proveedor **SimpleAPI**, key contratada hasta 31-07-2027; cuota API RUT 10/mes reservada a altas de proveedores (cliente con caché y control de cuota en `herramientas/sii-simpleapi/`) |
| DP-06 | Portal del proveedor | Cecilia | Abierta |
| DP-07 | Catálogo Aramark como productos | Cecilia + Partner | Abierta |
| DP-08 | Validación del TXT en Odoo antes de cargar al banco | Patricio | Abierta |
| DP-09 *(nueva)* | Proveedores en Zoho: módulo separado vs tipo de cuenta en Socios | Patricio + Alexander | Abierta |

---

**Preparado por:** José Ramón Jottar — JR Jottar Consultoría
**Pendiente de validación por:** Patricio Fernández (Adm. y Finanzas) · Cecilia Ramírez (OC/Compras)
