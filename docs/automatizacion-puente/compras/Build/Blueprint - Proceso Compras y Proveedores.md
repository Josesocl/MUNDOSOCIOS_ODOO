# Blueprint — Proceso Compras y Proveedores (Zoho CRM)

**Fecha:** 2026-07-02 · Para el implementador. Crear en `Setup → Automation → Blueprint`, sobre el módulo `Ordenes_Compra` (el estado de `Solicitudes` se mueve en paralelo con su propio Blueprint más simple, ver §2).
Referencias: `Especificacion modulos Zoho CRM.md` (campos), `Borradores Deluge.md` (funciones), `Fase 0/Politica de aprobaciones de compras.md` (matriz).

---

## 1. Vista general — los 10 estados

```
Solicitud → Cotización → En aprobación → Aprobada → Proveedor validado
→ OC emitida → Facturada → Recepción conforme → En pago → Pagada
```

Los primeros 2 estados (Solicitud, Cotización) viven principalmente en el registro de `Solicitudes`; desde "En aprobación" en adelante, el estado relevante es el de `Ordenes_Compra` (que ya tiene lookup a la `Solicitud` de origen). En la práctica, ambos módulos comparten la misma etiqueta de estado para que el solicitante vea un único avance de punta a punta.

---

## 2. Detalle por transición

### 2.1 Solicitud → Cotización
- **Quién la ejecuta:** el área requirente o quien gestiona las cotizaciones (hoy Cecilia).
- **Criterio de entrada (obligatorio para avanzar):** existe al menos un registro en `Cotizaciones` vinculado a esta `Solicitud`.
- **Campos obligatorios antes de avanzar:** `Cotizaciones.Monto_cotizado`, `Cotizaciones.Adjunto` (la cotización del proveedor).
- **Función Deluge:** ninguna. Transición manual (botón "Mover a Cotización" en el Blueprint).

### 2.2 Cotización → En aprobación
- **Quién la ejecuta:** quien gestiona las cotizaciones, una vez elegida la mejor alternativa.
- **Criterio de entrada:** debe existir una `Cotización` de esa `Solicitud` con `Seleccionada = true`, y `Solicitudes.Motivo_de_seleccion` no vacío.
- **Al entrar a este estado se crea (o se actualiza) el registro de `Ordenes_Compra`** con: `Solicitud` (lookup), `Proveedor` (desde la cotización seleccionada), `Monto_bruto_c_IVA` (calculado: `Cotizaciones.Monto_cotizado` × 1.19 si el monto cotizado es neto — confirmar con Patricio si las cotizaciones que hoy se reciben vienen netas o brutas), `Centro_de_costo`, `Cuenta_contable` (heredados de la Solicitud).
- **Función Deluge que dispara al crear la OC:** `resolverAprobador(ocId)` — calcula el tramo y escribe `Aprobador_asignado_1/2`.
- **Acción común del Blueprint:** enviar notificación al `Aprobador_asignado_1`.

### 2.3 En aprobación → Aprobada
- **Quién la ejecuta:** el motor de Approval Process (automático), no una persona moviendo el registro a mano.
- **Criterio de entrada:**
  `Resultado_aprobacion_1 = "Aprobada"` **Y** (`Resultado_aprobacion_2 = "Aprobada"` **O** `Resultado_aprobacion_2 = "No aplica"`)
- **Si `Resultado_aprobacion_1 = "Rechazada"` o `Resultado_aprobacion_2 = "Rechazada"`:** la OC va a un estado terminal `Rechazada` (fuera de los 10 estados "felices" — agregar como estado adicional del Blueprint, sin más transiciones salvo "Reabrir" que vuelve a "Cotización").
- **Configuración del Approval Process (fuera del Blueprint, en `Setup → Automation → Approval Process` sobre `Ordenes_Compra`):**
  - Criterio de entrada al proceso: todos los registros (toda OC pasa por aprobación).
  - Nivel 1 — Aprobador: campo `Aprobador_asignado_1`. Acción "On Approve": `Resultado_aprobacion_1 = "Aprobada"`. Acción "On Reject": `Resultado_aprobacion_1 = "Rechazada"`.
  - Nivel 2 (condicional) — Aprobador: campo `Aprobador_asignado_2`. Zoho salta este nivel automáticamente si el campo está vacío (tramos sin doble firma). Mismas acciones On Approve/On Reject sobre `Resultado_aprobacion_2`.
- **Función Deluge:** ninguna adicional — el Approval Process actualiza los campos directamente.

### 2.4 Aprobada → Proveedor validado
- **Quién la ejecuta:** automático (Blueprint transition condition), o manual si el proveedor ya estaba Apto de antes.
- **Criterio de entrada:** `Ordenes_Compra.Proveedor.Estado_proveedor = "Apto"`.
- **Si el proveedor NO está Apto:** la OC queda "atascada" en este paso — es la señal correcta de que primero hay que completar la Ficha de Proveedor (datos bancarios + verificación SII). El Blueprint debe mostrar un mensaje de ayuda ("Proveedor en validación — revisar Situación SII y datos bancarios antes de continuar").
- **Función Deluge que puede disparar en este punto:** `actualizarVerificacionSII(provId)`, si no se disparó antes al crear/editar el proveedor (ver §2 de Borradores Deluge.md). Lo ideal es que ya se haya ejecutado antes (on create/edit del Proveedor), y este paso solo *lea* el resultado.

### 2.5 Proveedor validado → OC emitida
- **Quién la ejecuta:** quien emite la OC en Manager+ (hoy, análogo al rol de Cecilia).
- **Antes de esta transición se ejecuta `exportarProveedorManager(provId)`** (botón "Generar archivos para Manager+" en el Blueprint) — genera los 3 CSV (Proveedor/Contactos/Cuenta bancaria) para cargar en Manager+ si el proveedor es nuevo. Si el proveedor ya existe en Manager+, se omite este paso.
- La persona emite la OC en Manager+ manualmente y **completa a mano** el campo `N° OC Manager` en Zoho.
- **Criterio de entrada:** `N° OC Manager` no vacío.
- **Función Deluge:** `exportarOCManager(ocId)` — genera el archivo de OC para Manager+, disparado al confirmar esta transición.

### 2.6 OC emitida → Facturada
- **Quién la ejecuta:** manual, cuando llega la factura del proveedor (vía Acepta a Manager+; hoy no hay integración Acepta↔Zoho).
- **Criterio de entrada:** campo `N° Factura` (agregar a `Ordenes_Compra` si no existe) no vacío, más `Fecha_factura`.
- **Función Deluge:** ninguna (Acepta no está integrado a Zoho en esta fase; ver Entregable 3, RF-07).

### 2.7 Facturada → Recepción conforme
- **Quién la ejecuta:** el área que solicitó originalmente el bien/servicio.
- **Criterio de entrada:** `Recepción_conforme = true`, `Fecha_recepción` y `Responsable_recepción` completos.
- **Función Deluge:** ninguna. Recordatorio automático configurado como Workflow Rule (no Blueprint) — ver `Workflow Rules - Alertas y Recordatorios.md`, Reglas 4 y 5.

### 2.8 Recepción conforme → En pago
- **Quién la ejecuta:** Tesorería, al incluir el documento en la próxima nómina de pago (`03_Control_Nomina_Pago_MundoSocios.xlsx`).
- **Criterio de entrada:** ninguno adicional — es automático apenas se cumple 2.7. (La validación real de que el documento "puede pagarse" ya ocurrió en la Ficha de Proveedor y en la planilla de Control de Nómina, fuera de Zoho.)
- **Función Deluge:** ninguna.

### 2.9 En pago → Pagada
- **Quién la ejecuta:** manual, una vez que Tesorería confirma el abono en el banco (no hay forma de leer esto automáticamente de Manager+/banco).
- **Criterio de entrada:** campo `Fecha_pago` completo.
- **Función Deluge:** ninguna.

---

## 3. Estado adicional fuera de la línea feliz: `Rechazada`
- **Se llega desde:** "En aprobación", si cualquiera de los 2 niveles de aprobación rechaza.
- **Transición de salida:** "Reabrir" → vuelve a "Cotización" (permite volver a cotizar con otro proveedor o ajustar el monto) — **no** vuelve directo a "En aprobación" para evitar reenviar sin cambios.
- **Campo obligatorio al reabrir:** `Motivo_rechazo` (agregar a `Ordenes_Compra`), para que quede registrado por qué no se aprobó.

---

## 4. Blueprint de `Solicitudes` (más simple, en paralelo)
`Solicitudes` solo necesita 2 estados propios: `Solicitud` → `Cotización`. A partir de "En aprobación", el estado que manda es el de `Ordenes_Compra` (la Solicitud puede reflejarlo con un campo de fórmula que traiga `Ordenes_Compra.Estado` vía lookup inverso, para que quien mira la Solicitud original no tenga que ir a buscar la OC).

---

## 5. Resumen de disparadores Deluge por transición

| Transición | Función Deluge | Dispara sobre |
|---|---|---|
| Cotización → En aprobación (creación de OC) | `resolverAprobador` + `validarPresupuesto` | `Ordenes_Compra` |
| Al crear/editar `Proveedores` (en cualquier momento, no ligado a una transición puntual) | `actualizarVerificacionSII` | `Proveedores` |
| Proveedor validado → OC emitida | `exportarProveedorManager` (si el proveedor es nuevo) | `Proveedores` |
| Proveedor validado → OC emitida | `exportarOCManager` | `Ordenes_Compra` |
| Recordatorios (aprobación pendiente, recepción conforme pendiente) | Sin Deluge — Workflow Rules time-based, ver `Workflow Rules - Alertas y Recordatorios.md` | `Ordenes_Compra` |

---

## 6. Pendientes antes de configurar en Zoho real
- [ ] Confirmar con Patricio si las cotizaciones se reciben netas o brutas (afecta el cálculo de `Monto_bruto_c_IVA` en §2.2).
- [x] ~~Agregar a `Ordenes_Compra` los campos `N° Factura`, `Fecha_factura`, `Fecha_pago`, `Motivo_rechazo`~~ — ya incorporados en `Especificacion modulos Zoho CRM.md` (2026-07-02).
- [x] ~~Decidir si el recordatorio de recepción conforme (§2.7) se implementa ahora~~ — especificado en `Workflow Rules - Alertas y Recordatorios.md` (2026-07-02), junto con el recordatorio de aprobación pendiente y la alerta de presupuesto (Task 2.5 del plan).
- [ ] Probar el comportamiento real de "salto de nivel 2 si el aprobador está vacío" en el Approval Process — es el comportamiento documentado de Zoho, pero conviene confirmarlo en sandbox antes de depender de él en producción.
