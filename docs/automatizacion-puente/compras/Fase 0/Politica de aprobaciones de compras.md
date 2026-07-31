# Política de aprobaciones de compras — MundoSocios

**Versión:** 1.0 · **Fecha:** 2026-06-18 · **Responsable:** Patricio Fernández (Adm. y Finanzas)
**Estado:** borrador para validación

## 1. Objetivo
Definir quién autoriza una compra según su monto, de forma **paramétrica** (los umbrales y aprobadores se pueden ajustar sin rehacer el proceso).

## 2. Base de cálculo
- El monto que define el tramo es el **total bruto, con IVA**, de la Orden de Compra (CLP).
- Si una solicitud se divide en varias OC, **cada OC** se evalúa por su propio monto. No se permite fraccionar una compra para evadir un tramo de aprobación.

## 3. Tramos de aprobación

| Tramo (CLP bruto c/IVA) | Aprobador requerido |
|---|---|
| Hasta $500.000 | Dueño del presupuesto (según centro de costo) |
| $500.001 – $1.000.000 | Cecilia Ramírez |
| $1.000.001 – $5.000.000 | Patricio Fernández (Adm. y Finanzas) |
| Sobre $5.000.000 | **Doble firma:** Patricio Fernández **y** Constanza Daniels (Gerente General) |

## 4. Reglas de borde
- **"Dueño del presupuesto"** se resuelve por el **centro de costo / línea de negocio / proyecto** indicado en la solicitud.
- **Doble firma:** ambas aprobaciones son obligatorias y **secuenciales** — primero Patricio Fernández, luego Constanza Daniels. Si cualquiera rechaza, la OC no avanza.
- **Subrogancia:** ante ausencia de un aprobador, se designa un reemplazo formal documentado (no se omite el control).
- **Reapertura:** si una OC aprobada cambia de monto y sube de tramo, vuelve a requerir la aprobación del tramo superior.

## 5. Parametrización
Estos valores viven en la tabla `Parametros_Aprobacion` de Zoho CRM (monto desde / monto hasta / aprobador 1 / aprobador 2 / activo). Cambiar un umbral o un aprobador se hace **editando esa tabla**, sin modificar el Blueprint ni el flujo.

## 6. Validación
- [ ] Patricio Fernández valida tramos y reglas de borde.
- [ ] Se confirman los nombres/usuarios Zoho de cada aprobador y de los dueños de presupuesto por centro de costo.
