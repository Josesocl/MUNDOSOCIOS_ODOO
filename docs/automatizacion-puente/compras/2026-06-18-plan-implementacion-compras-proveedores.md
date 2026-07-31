# Plan de implementación — Automatización Compras y Proveedores (sistema puente)

> **⚠️ FUERA DE ALCANCE (decisión del cliente, 2026-07-06):** MundoSocios decidió no construir la capa Zoho CRM. **Solo FASE 0 (abajo) sigue vigente**; las Tasks 1.1–1.10 (Fase 1) y 2.0–2.5 (Fase 2) quedan como referencia histórica, no se van a ejecutar por ahora. Lo que reemplaza a Fases 1-2 en el alcance actual son las 5 herramientas de `Herramientas Operativas/` y el `Validador SII (Python standalone)/`. Ver `Build/00_INDICE - Guia de implementacion.md` §5.

> **Para el implementador:** ejecutar tarea por tarea. Los pasos usan checkboxes (`- [ ]`). Este es un proyecto de **configuración** (Zoho CRM/Forms, SharePoint, archivos Manager+, Deluge); la verificación de cada tarea es un **criterio de aceptación** comprobable en la herramienta, no una prueba unitaria. No hay repositorio git.

**Goal:** Implementar un sistema puente que dé trazabilidad y aprobaciones automáticas al proceso de Compras y Proveedores de MundoSocios sobre Zoho CRM, manteniendo Manager+ (contable) y SharePoint (documental), antes de migrar a Odoo.

**Architecture:** 3 capas — Zoho CRM (orquestación/estado), Manager+ (registro contable, integrado por archivo export/import), SharePoint (respaldo documental). Zoho es la fuente de verdad del *estado*; no duplica el dato contable.

**Tech Stack:** Zoho CRM (módulos personalizados, Blueprint, Approval Processes, Workflow Rules, Deluge), Zoho Forms, SharePoint MundoSocios, validación SII vía HTTP (Deluge), archivos CSV/Excel/TXT para Manager+.

**Operación productiva:** corre con cuentas MundoSocios. Owner funcional: Patricio Fernández. Respaldo SharePoint con su cuenta. Parametrizar todos los owners/usuarios (aprobadores, remitente de notificaciones, dueño del respaldo) — nunca cuentas del consultor.

**Referencia:** spec `2026-06-18-automatizacion-compras-proveedores-design.md` (misma carpeta).

---

## Estructura de artefactos

**Zoho CRM — módulos personalizados a crear:**
- `Proveedores` — maestro de proveedores (responsable del dato de proveedor en la capa de orquestación).
- `Solicitudes` — solicitud de compra del área requirente (origen del proceso).
- `Cotizaciones` — cotizaciones asociadas a una Solicitud (lookup a Solicitudes).
- `Ordenes_Compra` — registro/espejo de la OC: N° OC de Manager+, monto, link SharePoint, estado (lookup a Solicitudes y Proveedores).
- `Parametros_Aprobacion` — tabla paramétrica de umbrales y aprobadores (editable sin tocar el Blueprint).

**Zoho Forms:** formulario `Solicitud de Compra` → inserta en módulo `Solicitudes`.

**Deluge (funciones):** `validarSII`, `exportarProveedorManager`, `exportarOCManager`.

**SharePoint:** biblioteca `Compras` con estructura por expediente; el link se guarda en `Ordenes_Compra`.

**Documentos de gobierno (Fase 0):** política de aprobaciones, checklist de campos críticos del proveedor, plantilla de OC, convención de carpetas.

---

## FASE 0 — Estandarización (01–15 jul) · sin software nuevo

### Task 0.0: Habilitar cuentas y accesos MundoSocios

**Artefactos:** documento `Accesos y cuentas.md`; tickets/solicitudes a TI MundoSocios.

- [ ] **Step 1: Listar identidades requeridas**
  Documentar: usuarios Zoho CRM para aprobadores (dueños de presupuesto, Cecilia Ramírez, Patricio Fernández, Constanza Daniels) y operadores; cuenta owner de SharePoint (Patricio Fernández); buzón remitente de notificaciones MundoSocios.
- [ ] **Step 2: Solicitar accesos**
  Enviar la lista a TI/Patricio para habilitar permisos sobre la biblioteca documental MundoSocios y licencias Zoho CRM de los aprobadores.
- [ ] **Step 3: Verificación**
  Criterio: cada identidad existe, puede iniciar sesión y tiene el permiso mínimo necesario. Registrar confirmación de Patricio.

### Task 0.1: Documentar la política de aprobaciones (paramétrica)

**Artefactos:** `Politica de aprobaciones.md`.

- [ ] **Step 1: Escribir la tabla de tramos**
  Montos en CLP bruto (con IVA):
  | Tramo | Aprobador |
  |---|---|
  | Hasta 500.000 | Dueño del presupuesto |
  | 500.001 – 1.000.000 | Cecilia Ramírez |
  | 1.000.001 – 5.000.000 | Patricio Fernández |
  | Sobre 5.000.000 | Doble firma: Patricio Fernández + Constanza Daniels |
- [ ] **Step 2: Definir reglas de borde**
  Documentar: el monto de comparación es el total bruto c/IVA de la OC; "dueño del presupuesto" se resuelve por centro de costo; doble firma = ambas aprobaciones obligatorias y secuenciales (Patricio → Constanza).
- [ ] **Step 3: Verificación**
  Criterio: Patricio valida por escrito que la tabla y las reglas de borde son correctas.

### Task 0.2: Checklist de campos críticos del proveedor

**Artefactos:** `Checklist proveedor.md` (insumo de los campos del módulo Proveedores y del archivo Manager+/TXT).

- [ ] **Step 1: Listar los campos obligatorios para no romper el TXT bancario**
  Razón social, RUT, giro, banco, tipo de cuenta, N° de cuenta, email de pago/contacto, forma y plazo de pago, situación SII vigente.
- [ ] **Step 2: Marcar cuáles bloquean el avance**
  Definir qué campos son obligatorios para pasar de "proveedor en validación" a "proveedor apto".
- [ ] **Step 3: Verificación**
  Criterio: el checklist cubre todos los campos que hoy, si faltan, hacen fallar la nómina/TXT (confirmar contra un caso real con Adm. y Finanzas).

### Task 0.3: Rediseñar formulario de Solicitud (Zoho Forms)

**Artefactos:** formulario `Solicitud de Compra` en Zoho Forms.

- [ ] **Step 1: Definir campos obligatorios**
  Área/solicitante, descripción, cantidad, fecha requerida, presupuesto estimado, centro de costo / línea de negocio / proyecto, cuenta contable, proveedor sugerido, motivo de selección, adjunto de cotizaciones.
- [ ] **Step 2: Construir el formulario** en Zoho Forms con esos campos marcados como requeridos.
- [ ] **Step 3: Verificación**
  Criterio: el formulario no permite enviar si falta un campo obligatorio; un envío de prueba llega completo.

### Task 0.4: Estructura de carpetas SharePoint y plantilla de OC

**Artefactos:** biblioteca `Compras` en SharePoint MundoSocios; plantilla `OC.docx`/`OC.xlsx`.

- [ ] **Step 1: Definir convención de carpetas**
  `Compras/{AAAA}/{N° OC}/` con: formulario Zoho, cotizaciones, OC, factura, correo de recepción conforme.
- [ ] **Step 2: Crear la plantilla única de OC** con los campos contables que hoy se piden por correo a Cecilia.
- [ ] **Step 3: Verificación**
  Criterio: se crea una carpeta de expediente de prueba con la plantilla y la cuenta de Patricio puede leer/escribir en ella.

---

## FASE 1 — Proceso y aprobaciones en Zoho CRM (jul–ago)

> Navegación Zoho: `Setup → Customization → Modules and Fields` para módulos; `Setup → Automation → Approval Processes`, `… → Workflow Rules`, `… → Blueprint`.

### Task 1.1: Módulo `Proveedores`

**Artefactos:** módulo personalizado `Proveedores`.

- [ ] **Step 1: Crear el módulo** `Proveedores`.
- [ ] **Step 2: Crear campos** según `Checklist proveedor.md` (Task 0.2): Razón social (texto), RUT (texto único), Giro, Banco (picklist), Tipo de cuenta (picklist), N° cuenta (texto), Email pago (email), Forma de pago (picklist), Plazo de pago (número), Situación SII (picklist: Vigente/No vigente/Pendiente), Estado proveedor (picklist: En validación/Apto/Rechazado).
- [ ] **Step 3: Marcar RUT como campo único** para evitar duplicados.
- [ ] **Step 4: Verificación**
  Criterio: se crea un proveedor de prueba; intentar crear otro con el mismo RUT es rechazado por el sistema.

### Task 1.2: Módulo `Solicitudes`

**Artefactos:** módulo `Solicitudes`.

- [ ] **Step 1: Crear el módulo** `Solicitudes`.
- [ ] **Step 2: Crear campos**: Solicitante, Descripción, Cantidad, Fecha requerida, Presupuesto estimado (moneda), Centro de costo (picklist), Cuenta contable (picklist), Proveedor sugerido (lookup a `Proveedores`), Motivo de selección, Estado (picklist con los 10 estados del flujo).
- [ ] **Step 3: Verificación**
  Criterio: se crea una solicitud manual de prueba con todos los campos.

### Task 1.3: Módulo `Cotizaciones`

**Artefactos:** módulo `Cotizaciones`.

- [ ] **Step 1: Crear el módulo** `Cotizaciones` con lookup a `Solicitudes` y a `Proveedores`.
- [ ] **Step 2: Crear campos**: Monto cotizado (moneda), Plazo de entrega, Adjunto, Seleccionada (checkbox).
- [ ] **Step 3: Verificación**
  Criterio: a una solicitud se le asocian 2 cotizaciones y se marca una como seleccionada.

### Task 1.4: Módulo `Ordenes_Compra`

**Artefactos:** módulo `Ordenes_Compra`.

- [ ] **Step 1: Crear el módulo** con lookup a `Solicitudes` y `Proveedores`.
- [ ] **Step 2: Crear campos**: N° OC Manager (texto), Monto bruto c/IVA (moneda), Centro de costo, Cuenta contable, Link expediente SharePoint (URL), Estado (picklist: los 10 estados), Aprobador asignado, Resultado aprobación.
- [ ] **Step 3: Verificación**
  Criterio: se crea una OC de prueba ligada a una solicitud y un proveedor, con link SharePoint válido (abre la carpeta).

### Task 1.5: Conectar Zoho Forms → `Solicitudes`

**Artefactos:** integración Forms→CRM.

- [ ] **Step 1: Mapear** cada campo del formulario `Solicitud de Compra` al campo equivalente del módulo `Solicitudes`.
- [ ] **Step 2: Verificación**
  Criterio: un envío del formulario crea automáticamente un registro completo en `Solicitudes` con estado inicial "Solicitud".

### Task 1.6: Tabla paramétrica de aprobaciones

**Artefactos:** módulo `Parametros_Aprobacion`.

- [ ] **Step 1: Crear el módulo** `Parametros_Aprobacion` con campos: Monto desde (moneda), Monto hasta (moneda), Aprobador 1 (lookup a usuarios), Aprobador 2 (lookup a usuarios, opcional), Activo (checkbox).
- [ ] **Step 2: Cargar las 4 filas** de la política (Task 0.1).
- [ ] **Step 3: Verificación**
  Criterio: editar un umbral en este módulo no requiere tocar el Blueprint; los rangos no se solapan ni dejan huecos.

### Task 1.7: Ruteo de aprobación por tramo

**Artefactos:** Approval Process / Workflow Rules en `Ordenes_Compra`.

- [ ] **Step 1: Crear función Deluge `resolverAprobador`** que, dado el `Monto bruto c/IVA` y el `Centro de costo` de la OC, lea `Parametros_Aprobacion` y devuelva el/los aprobadores (resolviendo "dueño del presupuesto" por centro de costo).
- [ ] **Step 2: Disparar la función** en el workflow al pasar la OC a estado "En aprobación", escribiendo `Aprobador asignado`.
- [ ] **Step 3: Configurar Approval Process** que envíe a `Aprobador asignado`; si el tramo es doble firma, encadenar Patricio → Constanza.
- [ ] **Step 4: Verificación**
  Criterio: OC de $400.000 → dueño de presupuesto; $900.000 → Cecilia; $3.000.000 → Patricio; $8.000.000 → Patricio y luego Constanza (ambas obligatorias).

### Task 1.8: Blueprint del proceso (10 estados)

**Artefactos:** Blueprint sobre `Solicitudes`/`Ordenes_Compra`.

- [ ] **Step 1: Definir los estados**: Solicitud → Cotización → En aprobación → Aprobada → Proveedor validado → OC emitida → Facturada → Recepción conforme → En pago → Pagada.
- [ ] **Step 2: Definir transiciones** con campos obligatorios por etapa (p. ej. para salir de "Cotización" debe existir una cotización marcada como seleccionada; para "OC emitida" debe existir N° OC Manager).
- [ ] **Step 3: Verificación**
  Criterio: no se puede saltar de "Cotización" a "OC emitida" sin pasar por aprobación; cada transición exige sus campos.

### Task 1.9: Captura de recepción conforme

**Artefactos:** campo/sub-formulario en `Ordenes_Compra`.

- [ ] **Step 1: Agregar** campos: Recepción conforme (checkbox), Fecha recepción, Responsable recepción, Adjunto/correo.
- [ ] **Step 2: Bloquear** la transición a "En pago" si Recepción conforme no está marcada.
- [ ] **Step 3: Verificación**
  Criterio: una OC sin recepción conforme no puede avanzar a "En pago".

### Task 1.10: Dashboards

**Artefactos:** dashboard `Compras`.

- [ ] **Step 1: Crear vistas**: OC abiertas por estado, presupuesto consumido por centro de costo, tiempo promedio por etapa, aprobaciones pendientes.
- [ ] **Step 2: Verificación**
  Criterio: el dashboard refleja correctamente las OC de prueba creadas en tareas anteriores.

---

## FASE 2 — Integraciones (ago–sep)

### Task 2.0: Despejar formato de carga/exportación de Manager+

**Artefactos:** `Manager - formatos de archivo.md`.

- [ ] **Step 1: Confirmar con el equipo Manager+** qué entidades admiten carga/descarga masiva (proveedores, OC, documentos) y el layout exacto (columnas, encoding, separador).
- [ ] **Step 2: Documentar** un layout de ejemplo por entidad.
- [ ] **Step 3: Verificación**
  Criterio: existe un archivo de ejemplo por entidad que Manager+ acepta en una carga de prueba.

### Task 2.1: Función Deluge `validarSII`

**Artefactos:** función `validarSII` en Zoho CRM.

- [ ] **Step 0: Validación manual-asistida (Fase 1, ya operable)** — el SII oficial (`www2.sii.cl/stc/noauthz`) tiene fila de espera y captcha: NO es automatizable directo. Mientras tanto, el operador consulta el RUT (sin puntos, con dígito verificador) en el sitio SII y marca `Situación SII` en el proveedor.
- [ ] **Step 1: Elegir el servicio de validación para automatizar (Fase 2)** — API REST de terceros que envuelve la consulta de situación tributaria por RUT (candidatos: BaseAPI `baseapi.cl`, API Gateway `apigateway.cl`). Confirmar proveedor, costo y términos con MundoSocios. Documentar URL, método y credenciales.
- [ ] **Step 2: Escribir la función** (esqueleto Deluge):

```
string validarSII(string rut)
{
    respuesta = invokeurl
    [
        url: zoho.crm.getOrgVariable("sii_endpoint") + rut
        type: GET
        headers: {"Authorization": zoho.crm.getOrgVariable("sii_token")}
    ];
    estado = ifnull(respuesta.get("situacion"), "Pendiente");
    return estado;
}
```
  Guardar `sii_endpoint` y `sii_token` como variables de organización (no hardcodear).
- [ ] **Step 3: Disparar la función** en workflow al crear/editar un `Proveedor`, escribiendo el campo `Situación SII`.
- [ ] **Step 4: Verificación**
  Criterio: un RUT vigente conocido devuelve "Vigente"; un RUT inválido devuelve "No vigente"/"Pendiente" sin romper el flujo.

### Task 2.2: Exportador de alta de proveedor (`exportarProveedorManager`)

**Artefactos:** función `exportarProveedorManager`.

- [ ] **Step 1: Escribir** la función que toma un `Proveedor` en estado "Apto" y genera el archivo con el layout de Task 2.0.
- [ ] **Step 2: Entregar el archivo** (descarga o adjunto al registro / carpeta SharePoint) para carga en Manager+.
- [ ] **Step 3: Verificación**
  Criterio: el archivo generado se carga sin errores en Manager+ y crea el proveedor con todos los campos críticos.

### Task 2.3: Exportador de OC (`exportarOCManager`)

**Artefactos:** función `exportarOCManager`.

- [ ] **Step 1: Escribir** la función que genera el archivo de OC (layout Task 2.0) cuando la OC pasa a "Aprobada".
- [ ] **Step 2: Verificación**
  Criterio: el archivo se carga en Manager+ y genera la OC; el N° OC resultante se registra de vuelta en el campo `N° OC Manager`.

### Task 2.4: Reflejo de estados desde Manager+

**Artefactos:** procedimiento de actualización de estado.

- [ ] **Step 1: Definir** cómo se reflejan en Zoho los hitos que ocurren en Manager+ (facturada, en pago, pagada): carga de archivo de estados o actualización manual asistida.
- [ ] **Step 2: Verificación**
  Criterio: tras una carga/actualización, el estado en Zoho coincide con Manager+ para un set de OC de prueba.

### Task 2.5: Alertas de presupuesto y recordatorios

**Artefactos:** Workflow Rules.

- [ ] **Step 1: Alerta de presupuesto** — al aprobar, mostrar/validar el monto disponible del centro de costo y avisar si se excede.
- [ ] **Step 2: Recordatorios** — notificar aprobaciones pendientes (>X días) y OC sin recepción conforme.
- [ ] **Step 3: Verificación**
  Criterio: una OC que excede presupuesto dispara la alerta; una aprobación estancada genera recordatorio al aprobador.

---

## CIERRE PRE-ODOO (oct)

### Task C.1: Depurar maestro de proveedores

- [ ] **Step 1: Revisar** duplicados, RUT inválidos y campos críticos faltantes en `Proveedores`.
- [ ] **Step 2: Verificación**
  Criterio: 0 duplicados por RUT, 100% de proveedores "Apto" con campos críticos completos.

### Task C.2: Documentar procesos y reglas para migración

- [ ] **Step 1: Consolidar** estados, matriz de aprobaciones, validador SII y layouts de archivo en un documento de traspaso a Odoo.
- [ ] **Step 2: Verificación**
  Criterio: el documento permite a un implementador Odoo reconstruir el proceso sin consultar el detalle de Zoho.

---

## Self-review (cobertura del spec)

- Capa de orquestación (Zoho) → Tasks 1.1–1.10. ✔
- Capa contable (Manager+, por archivo) → Tasks 2.0, 2.2, 2.3, 2.4. ✔
- Capa documental (SharePoint) → Tasks 0.4, 1.4 (link). ✔
- Matriz de aprobaciones paramétrica §5.1 → Tasks 0.1, 1.6, 1.7. ✔
- Validación SII → Task 2.1. ✔
- Operación productiva / cuentas MundoSocios §8.1 → Task 0.0 + parametrización de owners en 1.7/2.1. ✔
- Activos portables a Odoo → Tasks C.1, C.2. ✔
- Restricción cchc.cl / archivo no API → premisas respetadas (Task 2.0 archivo; 0.0 accesos). ✔
