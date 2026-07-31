# Workflow Rules — Alertas y Recordatorios

**Fecha:** 2026-07-02 · Para el implementador. Crear en `Setup → Automation → Workflow Rules`, sobre el módulo `Ordenes_Compra`.
Cierra la **Task 2.5** del plan de implementación (alertas de presupuesto y recordatorios). Referencias: `Borradores Deluge.md` (funciones), `Especificacion modulos Zoho CRM.md` (campos), `Blueprint - Proceso Compras y Proveedores.md` (estados).

Regla general: **usar Workflow Rule sin código siempre que alcance** (Zoho lo resuelve nativo, sin riesgo de error de sintaxis); usar función Deluge **solo** cuando se necesita sumar/comparar registros relacionados (presupuesto) o llamar una API externa (SII, ya cubierto en `Borradores Deluge.md`).

---

## Regla 1 — Al crear la OC: resolver aprobador y validar presupuesto
- **Módulo:** `Ordenes_Compra`
- **Disparador:** "On Create" (se crea la OC al pasar de "Cotización" a "En aprobación", según el Blueprint §2.2)
- **Condición:** ninguna adicional — aplica a toda OC nueva
- **Acciones (en este orden):**
  1. Función personalizada: `resolverAprobador(ocId)`
  2. Función personalizada: `validarPresupuesto(ocId)`

> Las dos funciones son independientes entre sí (una resuelve quién aprueba, la otra si excede presupuesto) pero comparten el mismo disparador — no hace falta una regla por cada una.

---

## Regla 2 — Recordatorio de aprobación pendiente (Nivel 1)
- **Módulo:** `Ordenes_Compra`
- **Disparador:** Time-based — **2 días hábiles** después de `Fecha_entrada_aprobación` *(valor sugerido; ajustar según lo que Finanzas considere razonable)*
- **Condición:** `Estado = "En aprobación"` **Y** `Resultado_aprobacion_1 = "Pendiente"`
- **Acción:** Enviar correo (plantilla "Recordatorio de aprobación") a `Aprobador_asignado_1`, con copia a Patricio
- **Recurrencia:** repetir cada 2 días mientras la condición siga cumpliéndose (Zoho permite recurrencia en workflows time-based; si el aprobador aprueba/rechaza, la condición deja de cumplirse y la regla no se vuelve a disparar)

## Regla 3 — Recordatorio de aprobación pendiente (Nivel 2 — doble firma)
- **Módulo:** `Ordenes_Compra`
- **Disparador:** Time-based — 2 días hábiles después de `Fecha_entrada_aprobación`
- **Condición:** `Resultado_aprobacion_1 = "Aprobada"` **Y** `Resultado_aprobacion_2 = "Pendiente"`
- **Acción:** Enviar correo a `Aprobador_asignado_2` (será Constanza Daniels en los tramos que llegan a este nivel), con copia a Patricio
- **Nota:** esta regla solo aplica a OC en tramo >$5.000.000; en el resto, `Resultado_aprobacion_2 = "No aplica"` y la condición nunca se cumple.

---

## Regla 4 — Marcar fecha de entrada a "Facturada" (sin código)
- **Módulo:** `Ordenes_Compra`
- **Disparador:** "On Edit" cuando `Estado` cambia a `"Facturada"`
- **Condición:** `Estado = "Facturada"`
- **Acción:** Field Update — `Fecha_entrada_facturada` = fecha/hora actual
- Esta regla es la que le da al Recordatorio (Regla 5) una fecha base para contar los días.

## Regla 5 — Recordatorio de recepción conforme pendiente
- **Módulo:** `Ordenes_Compra`
- **Disparador:** Time-based — **5 días** después de `Fecha_entrada_facturada` *(mismo plazo que ya se documentó en el Blueprint §2.7)*
- **Condición:** `Estado = "Facturada"` **Y** `Recepción_conforme ≠ true`
- **Acción:** Enviar correo (plantilla "Recordatorio de recepción conforme") a `Solicitud.Solicitante`, con copia al área de Finanzas
- **Recurrencia:** repetir cada 3 días mientras la condición siga cumpliéndose

---

## Plantillas de correo a crear
| Plantilla | Usada en | Variables a incluir |
|---|---|---|
| "Recordatorio de aprobación" | Reglas 2 y 3 | N° Solicitud, Proveedor, Monto bruto, Centro de costo, link directo al registro |
| "Recordatorio de recepción conforme" | Regla 5 | N° OC Manager, Proveedor, Fecha factura, link directo al registro |
| "Alerta de presupuesto excedido" | Regla 1 (vía `sendmail` en `validarPresupuesto`, no es plantilla de Zoho sino texto armado en Deluge) | — |

## Pendientes de decisión
- [ ] Confirmar los plazos sugeridos (2 días para aprobación, 5 días para recepción conforme) con Patricio — son un punto de partida razonable, no un número ya validado con el equipo.
- [ ] Definir si la recurrencia de recordatorios debe tener un tope (ej. máximo 3 recordatorios) para no saturar al aprobador — Zoho lo permite configurar.
- [ ] Crear las 2 plantillas de correo en `Setup → Templates → Email Templates` antes de activar las Reglas 2, 3 y 5.
