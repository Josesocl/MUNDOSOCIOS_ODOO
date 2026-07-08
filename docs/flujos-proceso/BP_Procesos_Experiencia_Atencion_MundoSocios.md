# Blueprint — Área de Experiencia y Atención Integral al Socio

**Insumo para implementación Odoo Enterprise**
**Proyecto:** Implementación Odoo Enterprise — MundoSocios CChC · **Fase:** Fase 0 — Levantamiento y Diseño
**Fuente:** Camila Rivas (Subgerente de Experiencia) · **Elaborado por:** JR Jottar Consultoría
**Versión:** 2.0 — 2026-07-08 · Borrador para validación

### Registro de cambios v2.0 (respecto de v1.0, julio 2026)
1. **Nueva exigencia en la inscripción de socios: certificado de Socio CChC** emitido por el portal de la Cámara (documento de referencia: `FLUJOS DE PROCESO/certificado Socio CChC Portal.pdf`), como respaldo obligatorio de la membresía vigente.
2. Valores de cuota social corregidos (1 UF persona / 3 UF empresa hasta 3 miembros + 1 UF adicional desde el 4º) — reemplazan los 1,44/0,48 UF de la v1.0.
3. Actores actualizados: sale Javiera Valdovinos; se incorporan reglas operativas de la capacitación de recaudación (reincorporación, traspasos de cuota, renuncias).

---

## 1. Propósito del documento
Formaliza el levantamiento de procesos del área de Experiencia y Atención Integral al Socio, a partir de las descripciones de Camila Rivas. Sirve como insumo directo para la fase de blueprint de la implementación Odoo. Para cada proceso: situación actual, flujo optimizado, mapeo a módulos Odoo, reglas de negocio y criterios UAT.

## 2. Contexto del área
El área gestiona tres frentes: incorporación de nuevos socios, atención integral (tickets, reembolsos, consultas) y la plataforma de experiencias/actividades. Hoy opera con WordPress, Google Forms, Google Sheets, correo y WhatsApp: procesos manuales, duplicación de datos y falta de trazabilidad.

**Interlocutores clave:** Camila Rivas (Subgerente de Experiencia) · Carla Carvajal (incorporación de socios, beneficiarios y traspasos de cuota) · equipo de Experiencias y Comunicaciones · embajadores de actividades. *(Javiera Valdovinos ya no está en MundoSocios.)*

## 3. Proceso: Inscripción de nuevo socio

### 3.1 Objetivo
Automatizar la incorporación de nuevos socios, minimizando tareas manuales, reduciendo tiempos de respuesta y asegurando desde el primer paso la **elegibilidad** (membresía CChC vigente, acreditada documentalmente).

### 3.2 Situación actual (AS-IS)
- El interesado completa un formulario en WordPress o Google Forms.
- Los datos se descargan manualmente a planilla.
- La validación de membresía CChC se hace manualmente y sin respaldo documental estandarizado.
- El enlace Webpay se envía por correo a mano; la confirmación va por correo/WhatsApp sin registro.
- No hay flujo de bienvenida ni activación automática en CRM.

### 3.3 Flujo optimizado (TO-BE)

| Etapa | Actor | Proceso | Estado | Módulo Odoo |
|---|---|---|---|---|
| 1. Inscripción | Socio | Completa formulario web **y adjunta el certificado de Socio CChC** (obligatorio, ver §3.4). Datos y adjunto quedan en CRM, estado "Pendiente de validación". | Pendiente de validación | Website + CRM |
| 2. Validación | Equipo MS | Verifica membresía CChC **contrastando el certificado adjunto** (RUT/razón social del certificado vs formulario, vigencia) además de la validación por RUT. Aprueba o rechaza desde CRM; el rechazo (incluido certificado inválido o vencido) envía correo automático indicando cómo obtenerlo en el portal CChC. | Aprobado / Rechazado | CRM |
| 3. Activación pago | Sistema | Al aprobar: envía enlace de pago (Webpay/pasarela), notifica a Finanzas, actualiza estado. | Pendiente de pago | CRM + Pagos |
| 4. Pago | Socio / Webpay | El socio paga; la pasarela confirma automáticamente. | Pago confirmado | Pagos |
| 5. Confirmación | Sistema | Estado "Socio Activo", comprobante al socio, confirmación a Finanzas (devengo). | Socio Activo | CRM + Contabilidad |
| 6. Bienvenida | Sistema | Correo de bienvenida: beneficios, acceso al Portal de Socios, canales. | Onboarding completo | Email Marketing |

### 3.4 Reglas de negocio
- Solo se admiten socios con **membresía CChC vigente**. La acreditación es doble:
  1. Validación por RUT contra la base CChC.
  2. **Certificado de Socio CChC obligatorio**, emitido por el portal de la Cámara (autoservicio del postulante; ejemplo de referencia: `certificado Socio CChC Portal.pdf`). Se adjunta en el formulario de inscripción y queda archivado en la ficha del socio.
  - ☐ Definir vigencia máxima aceptada del certificado (propuesta: emitido dentro de los últimos 30 días) y el tratamiento de postulantes que no pueden obtenerlo (canal de excepción con validación manual reforzada).
- El enlace de pago vence a los 7 días hábiles; vencido, la solicitud se cancela automáticamente con aviso.
- El primer pago corresponde a la cuota social vigente: **Persona 1 UF · Empresa 3 UF hasta 3 miembros + 1 UF adicional por cada miembro desde el 4º** (UF según regla de cierre enero/febrero/marzo — precisar con Finanzas).
- **Reincorporación:** un socio que dejó el programa y vuelve debe pagar la cuota del **año en que se reincorpora** y presentar comprobante; también debe adjuntar certificado CChC vigente.
- **Renuncias:** se procesan solo tras correo de confirmación del socio.
- **Cambio de empresa / beneficiarios:** el traspaso de cuota y la modificación de beneficiarios se gestionan internamente (Carla Carvajal); exigir certificado CChC actualizado de la nueva empresa.
- Finanzas recibe notificación de cada nuevo socio para el devengo.

### 3.5 Módulos Odoo involucrados
Website (formulario con **carga de archivo obligatoria** para el certificado) · CRM (lead → oportunidad → socio activo, con adjunto en la ficha) · Contactos · Pagos (Webpay vía pasarela) · Contabilidad (devengo automático) · Email Marketing (bienvenida) · Documents (archivo del certificado en el expediente del socio).

### 3.6 Criterios de aceptación UAT
1. Un formulario completado genera un lead en CRM con todos los campos poblados **y el certificado CChC adjunto**; el formulario **no permite enviar sin el adjunto**.
2. El validador puede ver el certificado desde el CRM y aprobar/rechazar; el rechazo por certificado inválido envía el correo con instrucciones del portal CChC.
3. La aprobación dispara el enlace de pago sin intervención manual.
4. El pago confirmado activa al socio y genera el asiento contable.
5. El socio recibe la bienvenida con acceso al portal en máximo 5 minutos post-pago.
6. El certificado queda archivado y consultable en la ficha del socio (auditoría de elegibilidad).

## 4. Proceso: Reembolsos de Exámenes Preventivos

### 4.1 Situación actual (AS-IS)
Documentos por correo/WhatsApp; revisión en bandejas personales; sin estados ni seguimiento; comunicación informal del resultado.

### 4.2 Flujo optimizado (TO-BE)
| Etapa | Actor | Proceso | Estado | Módulo |
|---|---|---|---|---|
| 1. Solicitud | Socio | Formulario en el Portal con adjuntos (bono, comprobante, documentos). | Pendiente de revisión | Portal + Helpdesk |
| 2. Notificación | Sistema | Aviso automático a Atención y Finanzas. | Pendiente de revisión | Helpdesk |
| 3. Revisión | Atención | Revisa documentación; aprueba u observa (pide información al socio). | Aprobada / Observada | Helpdesk |
| 4. Activación pago | Sistema | Notifica a Finanzas, informa plazo al socio. | Pendiente de pago | Helpdesk + Contabilidad |
| 5. Reembolso | Finanzas | Transferencia según procedimiento interno. | Pago procesado | Contabilidad |
| 6. Confirmación | Sistema | Estado "Reembolso pagado" + aviso al socio. | Reembolso pagado | Helpdesk |

**UAT:** solicitud con adjuntos desde el portal · ticket visible para Atención y Finanzas con estados diferenciados · notificaciones automáticas en cada cambio de estado.

## 5. Proceso: Registro y Gestión de Atenciones a Socios
Flujo TO-BE (sin cambios v1.0): recepción omnicanal registrada en ficha única → ticket con número/canal/motivo → asignación automática → gestión registrada en CRM → seguimiento con SLA (primera respuesta 24 h hábiles; escalamiento a jefatura a las 48 h) → resolución → cierre con encuesta CSAT (24 h después) → dashboard.
**Módulos:** Helpdesk (tickets, SLA), CRM/Contactos, Encuestas, WhatsApp (omnicanal, si aplica), Dashboards.
*(Nota operativa 2026-07: durante ausencias del titular de recaudación, las consultas de socios sobre pagos/comprobantes se responden con copia a Recaudación — hoy Fran con c/c a Oriana. El TO-BE resuelve esto con el ticket omnicanal.)*

## 6. Proceso: Gestión de Experiencias e Inscripciones
Sin cambios de fondo respecto de v1.0:
- **Viaje 1 — Administrador:** actividad en Eventos (fechas, cupos, valores socio/acompañante, acceso: exclusiva socios / socios+familiares / público general), formulario personalizable con lógica condicional, acompañantes configurables, T&C por actividad, publicación automática (landing, URL única, QR).
- **Viaje 2 — Socio:** catálogo con filtros → validación por RUT con autocompletado (socio/familiar; registro manual si es actividad abierta) → inscripción + acompañantes → T&C + pago en línea → confirmación con calendario y comprobante → correos automáticos (participante y Finanzas).
- **Viaje 3 — Gestión interna:** 5 perfiles (Administrador, Experiencias, Comunicaciones, Finanzas, Embajadores), dashboard de actividades, check-in manual/QR en tiempo real, exportaciones y reportes.
- **Desarrollos a evaluar con el partner:** formularios dinámicos con lógica condicional, autocompletado por RUT, generación automática de formatos de imagen, acompañantes con datos diferenciados, check-in QR en tiempo real, descuento por número de actividades.
- **UAT:** publicar una actividad en <10 min · inscripción con autocompletado en <3 min · pago genera asiento y aviso a Finanzas sin intervención · dashboard en tiempo real · correos automáticos sin configuración adicional.

## 7. Decisiones pendientes para validar
| # | Decisión | Opciones | Responsable |
|---|---|---|---|
| DP-01 | Portal del socio: Odoo nativo vs híbrido con WordPress | Nativo / Híbrido | Constanza + Camila |
| DP-02 | Pasarela de pago para experiencias | Nuvei / Toku / Webpay | Patricio + Constanza |
| DP-03 | Formularios dinámicos: ¿Studio basta? | Studio / Custom | Partner |
| DP-04 | Check-in QR: custom vs app de terceros | Custom / Terceros | Partner + Camila |
| DP-05 | Reembolsos: Helpdesk vs CRM extendido | Helpdesk / CRM | Camila + JR |
| DP-06 | Formatos de imagen automáticos: ¿MVP? | MVP / Fase 2 | Camila + Partner |
| DP-07 | Descuentos por nº de actividades: ¿nativo? | Pricelists / Dev | Partner |
| DP-08 *(nueva)* | Certificado Socio CChC: vigencia máxima aceptada y canal de excepción; ¿validación automática futura contra el portal CChC (API) o siempre documental? | 30 días / otro · API / documental | Camila + Constanza |

---

**Preparado por:** José Ramón Jottar — JR Jottar Consultoría · Contraparte del proyecto Odoo — MundoSocios CChC
**Pendiente de validación por:** Camila Rivas — Subgerente de Experiencia, MundoSocios
