# Índice y guía de implementación — Sistema puente Compras y Proveedores (Zoho CRM)

> **⚠️ FUERA DE ALCANCE (decisión del cliente, 2026-07-06):** MundoSocios decidió no construir este paquete Zoho CRM. Toda la carpeta `Build/` queda como **referencia histórica**. El alcance vigente hoy es Fase 0 + `Herramientas Operativas/` + `Validador SII (Python standalone)/` — ver §5 más abajo (que ya describía esta relación) y `2026-06-18-plan-implementacion-compras-proveedores.md` (banner al inicio).

**Fecha:** 2026-07-02 · Punto de entrada para quien vaya a implementar este paquete en Zoho CRM.

## 0. Qué es este paquete
Especificación completa del proceso de **Compras y Proveedores end-to-end** (solicitud → cotización → creación proveedor → OC → recepción factura → nómina/pago → conciliación) como "sistema puente" sobre Zoho CRM. No requiere Creator ni Flow — solo módulos personalizados, Blueprint, Approval Process, Workflow Rules y funciones Deluge, que sí están disponibles en Zoho CRM base.

**No es** una instalación lista para copiar y pegar sin revisión: varios puntos quedaron marcados explícitamente como "a confirmar" (§4) porque dependen de datos que solo Patricio/el equipo de MundoSocios tiene, o de comportamientos de Zoho que solo se pueden verificar en una cuenta real (no hay forma de ejecutar Deluge ni de probar un Blueprint fuera de Zoho).

---

## 1. Documentos de este paquete (orden de lectura sugerido)

| # | Documento | Qué define |
|---|---|---|
| 1 | `Especificacion modulos Zoho CRM.md` | Los 6 módulos personalizados y todos sus campos: `Proveedores`, `Solicitudes`, `Cotizaciones`, `Ordenes_Compra`, `Parametros_Aprobacion`, `Presupuestos` |
| 2 | `Blueprint - Proceso Compras y Proveedores.md` | Los 10 estados del proceso (+1 `Rechazada`): quién ejecuta cada transición, criterio de entrada, campos obligatorios y qué función dispara |
| 3 | `Borradores Deluge.md` | Las 6 funciones Deluge: `resolverAprobador`, `validarSII` + `actualizarVerificacionSII`, `exportarProveedorManager`, `exportarOCManager`, `validarPresupuesto` |
| 4 | `Workflow Rules - Alertas y Recordatorios.md` | Las 5 reglas de notificación (alerta de presupuesto, recordatorios de aprobación y de recepción conforme) |

**Fuera de esta carpeta pero parte del mismo sistema:**
- `Fase 0/Formulario Zoho - Solicitud de Compra.md` — el formulario de intake (Zoho Forms → módulo `Solicitudes`).
- `Fase 0/Politica de aprobaciones de compras.md` — la matriz de montos que alimenta `Parametros_Aprobacion`.
- `Fase 0/Convencion de carpetas SharePoint.md` — cómo se arma el `Link expediente SharePoint` de cada OC.
- `Validador SII (Python standalone)/` — **alternativa a `validarSII`/`actualizarVerificacionSII` que no depende de Zoho.** Mismo problema (RUT + situación tributaria vía BaseAPI), pero en Python puro, ejecutable y con 37 tests automatizados verificados (a diferencia del Deluge, que no se puede probar fuera de una cuenta Zoho real). Útil como herramienta de verificación rápida hoy mismo, o como referencia de comportamiento correcto al implementar la versión Deluge.

---

## 2. Orden de implementación práctico en Zoho

1. **Crear los 6 módulos personalizados** (documento 1) con todos sus campos. Sin esto, nada de lo demás tiene dónde vivir.
2. **Cargar los datos base:**
   - `Parametros_Aprobacion`: las 4 filas de la matriz de aprobación (`Fase 0/Politica de aprobaciones de compras.md`).
   - `Presupuestos`: al menos el mes en curso, por centro de costo (requiere decidir primero quién lo mantiene — ver §4).
3. **Crear las variables de organización** (§3 de esta guía) — antes de escribir cualquier función Deluge que las use.
4. **Crear las 6 funciones Deluge** (documento 3), como Custom Functions.
5. **Configurar el Approval Process** de 2 niveles sobre `Ordenes_Compra` (detalle en `Blueprint...md` §2.3).
6. **Configurar el Blueprint** de 10 estados + `Rechazada` sobre `Ordenes_Compra` (documento 2), enlazando las funciones Deluge en las transiciones que corresponde.
7. **Configurar las 5 Workflow Rules** (documento 4), incluyendo las 2 plantillas de correo que piden.
8. **Construir el formulario Zoho Forms** de solicitud (`Fase 0/Formulario Zoho...md`) y mapearlo a `Solicitudes`.
9. **Probar de punta a punta** con 2-3 casos reales antes de anunciar el sistema al equipo: una OC de tramo bajo (aprobación simple), una de tramo alto (doble firma), y un proveedor nuevo (para probar `validarSII` + `exportarProveedorManager`).

---

## 3. Variables de organización a crear (consolidado)

| Variable | Para qué | Usada por |
|---|---|---|
| `sii_endpoint` | URL de la API de validación SII | `validarSII` |
| `sii_api_key` | Credencial de esa API | `validarSII` |
| `presupuesto_alerta_email` | Quién recibe la alerta de presupuesto excedido | `validarPresupuesto` |

---

## 4. Todo lo que quedó pendiente de confirmar o decidir (consolidado de los 4 documentos)

### A confirmar con Patricio (datos que solo él tiene)
- [ ] Las cotizaciones que hoy se reciben, ¿vienen **netas o brutas**? Afecta el cálculo de `Monto_bruto_c_IVA` al crear la OC.
- [ ] ¿El Importador de datos de Manager+ acepta crear **proveedores completos** (proveedor + contacto + cuenta bancaria), o solo "Comprobantes contables con documento" como hoy con los devengos? Define si `exportarProveedorManager` genera una carga masiva real o solo una ficha de apoyo para digitar.
- [ ] ¿Quién carga y mantiene mensualmente el módulo `Presupuestos`? Sin esto, la alerta de presupuesto no tiene con qué comparar (no bloquea nada, simplemente no alerta).
- [ ] Confirmar los plazos de los recordatorios (2 días para aprobación pendiente, 5 días para recepción conforme) — son un punto de partida razonable, no un número ya validado con el equipo.
- [ ] ¿Se automatiza también la verificación de **Dirección** y **Documentos DTE autorizados** contra el SII? El endpoint elegido (BaseAPI `/contribuyente`) no los entrega — requeriría otro endpoint del mismo proveedor u otra fuente.

### A decidir internamente (sin depender de un tercero)
- [ ] Si la recurrencia de los recordatorios debe tener un tope (ej. máximo 3 envíos) para no saturar al aprobador.
- [ ] Contratar BaseAPI o API Gateway para `validarSII` — quién aprueba el gasto y con qué frecuencia de uso estimada.

### A probar en un sandbox de Zoho real (no verificable desde este documento)
- [ ] `validarSII` con 3-5 RUT conocidos (uno vigente, uno sin inicio de actividades, uno inexistente) — el mapeo de campos de BaseAPI es el mejor esfuerzo de una investigación externa, no una prueba en vivo.
- [ ] El comportamiento de "saltar el nivel 2 del Approval Process si el aprobador está vacío" — es el comportamiento documentado de Zoho, pero conviene confirmarlo antes de depender de él.
- [ ] El patrón de formato de fecha `.toString("yyyy-MM")` usado por `validarPresupuesto`.
- [ ] `resolverAprobador` y `exportarOCManager` con casos reales de cada tramo de aprobación.
- [ ] `validarPresupuesto` con un centro de costo cargado a propósito por debajo del comprometido, para confirmar que llega la alerta.
- [ ] Crear las 2 plantillas de correo (`Setup → Templates → Email Templates`) antes de activar las Workflow Rules 2, 3 y 5.

---

## 5. Relación con el resto del proyecto

- **Ya operativo hoy, sin depender de nada de esto:** las 5 herramientas Excel de `Herramientas Operativas/` (Ficha de Proveedores, Registro de OC, Control de Nómina, UF/Cuota Social, Conciliación Bancaria). Este paquete de Zoho es la **evolución futura**, no un reemplazo inmediato — mientras no esté implementado y probado, el equipo sigue usando los Excel.
- **Documento relacionado:** `Entregables SOW/3 - Documento de requerimientos (area financiera).md`, RF-01 a RF-06b, ya resume estas mismas reglas en el lenguaje de requerimientos para quien implemente.
