# Entregable 1 — Informe de diagnóstico de procesos financiero-contables

**Cliente:** MundoSocios — CChC · **Consultor:** JR Jottar (IBS) · **Fecha:** 2026-06-23
**Estado:** borrador — a complementar/validar con las entrevistas a Patricio Fernández y equipo.
**Base documental:** levantamiento y manuales del área (carpeta `SHAREPOINT_ODOO/Levantamiento Adm. y Finanzas`).

---

## 1. Resumen ejecutivo
El área financiero-contable de MundoSocios opera sobre un ecosistema **fragmentado** (Zoho One, Manager+, Acepta, Banco de Chile, Webpay, Google Drive/Sheets, Excel, Outlook, WordPress) donde la integración entre sistemas es **manual o por archivo**. El proceso funciona, pero descansa fuertemente en **planillas intermedias**, **registro manual** y **conocimiento de personas específicas**, lo que genera retrabajo, errores recurrentes (especialmente en el TXT bancario y la conciliación) y baja trazabilidad. Es un área de **alta complejidad operativa** (~1.500 notas de cobro mensuales, ~233 movimientos por cartola, manejo de fondos propios vs. de terceros) y **crítica para la migración a Odoo**.

## 2. Inventario de herramientas y sistemas

| Sistema | Uso en el área | Rol |
|---|---|---|
| **Zoho One (CRM/Forms/Campaigns)** | Socios, beneficiarios, ticket de cuota social, formularios de solicitud | Front / registro comercial |
| **Manager+** | ERP contable: abastecimiento (compras/OC), finanzas (libro mayor, informes tributarios), tesorería (pagos, pago masivo, conciliación, anticipos), devengos | Sistema contable de registro |
| **Acepta (Sovos)** | Recepción de DTE / facturas; acuse y aceptación en SII antes de ingresar a Manager+ | Recepción documentos tributarios |
| **Banco de Chile** (cta. 8001104309) | Carga de **TXT** de transferencias; cartola para conciliación | Pagos y origen de conciliación |
| **Webpay (Transbank)** | Pago de cuota social y de actividades | Recaudación |
| **Manager+ — Importador/Exportador de datos** | Carga masiva por Excel (p. ej. devengos de seguros como "comprobantes contables con documento"); exportador de datos | **Vía de integración por archivo (ya en uso)** |
| **Google Sheets (Drive)** | "Listado de Proveedores MundoSocios", "Planilla de gastos y varios Solicitados 23-2024", control de nóminas, "DETALLE DE SOLICITUD DE COTIZACIONES 24", "Devengo Seguros Manager+", preconciliación, inscritos a actividades | Planillas operativas paralelas |
| **Excel / plantillas** | "Conciliación Manager", "Preconciliación", mantenedores de seguros, plan de cuentas | Cálculo y transformación |
| **OneDrive / SharePoint** | Respaldo documental (OC, factura, recepción) | Archivo |
| **Outlook** | Solicitudes, recepción conforme, derivaciones, cotizaciones | Comunicación / control informal |
| **SII (web)** — `zeus.sii.cl`, situación tributaria de terceros | Valor UF del día; validación de RUT/inicio de actividades | Consulta externa manual |
| **Proveedores de servicio externos** | Aramark (alimentación), Travel Security / Chicureo Travel (pasajes), hoteles (alojamiento) | Provisión vía solicitudes internas |
| **WordPress** | Web informativa + plataforma de experiencias/actividades | Front socios |

## 3. Mapa de procesos del área

### 3.1 Compras y cuentas por pagar
Solicitud (formulario Zoho/correo) → cotización manual (listado en Google Sheet) → OC solicitada por correo a Cecilia Ramírez → confección y aprobación por monto en Manager+ → recepción de factura vía Acepta → cuenta por pagar → validación de entrega por correo → respaldo en OneDrive → nómina de pago. *(Detalle en el spec de Compras y Proveedores.)*

### 3.2 Gestión de proveedores
Validación de RUT/situación tributaria en SII (manual) → creación en Manager+ con campos críticos para el TXT. Listado paralelo en Google Sheet.

### 3.3 Recepción y registro de facturas
Módulo Abastecimiento → Registro de compras Acepta → contabilización. Facturas sin OC se ingresan manualmente según presupuesto.

### 3.4 Boletas de honorarios (BOR)
Verificar proveedor tipo "honorario" y documento a nombre de MS → Abastecimiento → Ingresar documento → Boleta de honorario (con/sin retención, **13,75%**) → completar código de producto (= cuenta contable del gasto), centro de costo, línea de negocio, OT → contabilizar → registrar en planilla Drive (columnas C-K) para la próxima nómina y adjuntar PDF + cotización.

### 3.5 Nóminas de pago (proveedores)
**Todos los martes.** Se verifica que las facturas recibidas estén ingresadas en Manager+ y descritas en la planilla de control en Drive (dos secciones: historial del año y facturas pendientes de VB con comentarios). Tesorería → Pago masivo → emitir → descarga TXT → **abrir el TXT y editar a mano la fecha de pago** → cargar en Banco de Chile. Errores frecuentes documentados: anticipos/NC en negativo (no se pueden incluir, requieren ajuste previo), tipo de documento faltante, caracteres especiales o descripción >400, campos vacíos en el maestro → **el TXT falla**.

### 3.6 Rendiciones del equipo MS y nómina de personal
Rendiciones recibidas por correo/digital con respaldo → Tesorería → Documento → **RINDE** (tipo detalle Gasto o Anticipo Proveedor, cuenta exenta) → contabilizar → planilla Drive. Pago vía **Pago masivo a Personal** (tipo TRBP) → **segundo TXT** independiente del de proveedores → editar fecha → cargar en Banco de Chile.

### 3.7 Conciliación bancaria (mensual)
Verificar que los ingresos de cuota social tengan OT (los devengos no llevan OT) → descargar cartola del banco (PDF) → poblar plantillas "Preconciliación" y "Conciliación Manager" (Excel) → cuadrar cargos/abonos vs. cartola → importar a Manager+ (Tesorería → Conciliación bancaria, conciliación automática activada) → conciliar manualmente lo que no cuadra. Volumen típico: **~233 movimientos/cartola, ~78% automático, ~22% manual**. Casos especiales: convenios **PAC** (un documento ↔ varios abonos) y movimientos sin OT.

### 3.8 Recaudación y cobranza — cuota social
~1.500 notas de cobro mensuales. Incorporación de nuevos socios informada por correo (Carla Carvajal / Javiera Valdovinos) → cálculo del valor de cuota usando **UF del día extraída manualmente del SII** (Empresa 1,44 UF / Persona 0,48 UF) → correo al socio con plantilla y pago por Webpay/transferencia → recepción del pago → creación de **devengo de cuota social** en Manager+ → activar **ticket de cuota social** en Zoho → informar a Atención Integral al Socio.

### 3.9 Devengo de cuota social
Manual, en Finanzas → Comprobantes → comprobante de Traspaso de 2 líneas: DEBE `1150001 Cuota S. Empresa por Cobrar` (tipo doc CSEMP) / HABER `3210002 Cuota Social Empresa` (ingreso). Glosa: RUT + DEVENGO + CUOTA AÑO + CÁMARA. No lleva OT.

### 3.10 Carga de devengos de seguros (fondos de terceros)
Proceso mensual masivo: en carpeta Drive "Devengo Seguros Manager+" se copian los archivos del mes anterior por cada seguro (Plan Socios, Complementario, Catastrófico, Plan Carreño), se actualizan con el mantenedor (layout columnas A-V) y se cargan a Manager+ por **Mantenedores → Importador de datos → Comprobantes contables con documento (Excel)**. Cuentas por seguro (por cobrar / ingreso): Plan Socios 1130004/3310005, Complementario 1130003/3310003, Catastrófico 1130002/3310001, Plan Carreño 1130005/3310004. Si el socio no existe, el importador arroja error "Cliente no existe".

### 3.11 Fondos propios vs. fondos de terceros
La cuota social es **fondo propio**; los seguros (devengos 3.10) son **fondos de terceros** que se recaudan para pagar a las aseguradoras. La separación es contable (cuentas dedicadas) pero la operación descansa en planillas y disciplina manual; el riesgo de mezcla es alto.

### 3.12 Creación de clientes/socios
Mantenedores → Clientes/proveedores → tipo Cliente Nacional, clasificación = Cámara, sin giro, correo SII = correo del socio. Es prerrequisito del devengo y del importador de seguros.

### 3.13 Solicitudes internas (alimentan compras)
Sala, servicio de alimentación (Aramark), pasajes (Travel Security / Chicureo Travel) y alojamiento (hoteles). Todas entran por **formulario Zoho o correo**, se cotizan con el proveedor, se solicita la OC a Cecilia Ramírez (c/c Patricio Fernández), se registra en la planilla Drive "Gastos y varios Solicitados" y se cierra el caso en Zoho. Son el origen de buena parte de las OC.

## 4. Puntos críticos, cuellos de botella y riesgos

| # | Hallazgo | Tipo | Impacto |
|---|---|---|---|
| 1 | **TXT bancario frágil**: campos vacíos en el maestro de proveedor, caracteres especiales, descripciones >400, anticipos/NC en negativo y tipo de documento mal asignado hacen fallar el archivo | Error recurrente | Alto — retrasa pagos, retrabajo semanal |
| 2 | **Conciliación dependiente de planillas Excel intermedias** (preconciliación / conciliación manager) y ~22% manual; casos PAC y devengos sin OT | Cuello de botella | Alto — proceso mensual lento y propenso a error |
| 3 | **Doble registro**: planillas en Drive paralelas a Manager+; formulario web no integrado al CRM | Ineficiencia | Medio-alto — retrabajo y descuadres |
| 4 | **Dependencia de personas**: Cecilia (OC), Carla (incorporaciones), etc. | Riesgo operativo | Alto — bus factor |
| 5 | **Cálculo de UF manual** por cada incorporación desde la web del SII | Tarea manual repetitiva | Medio |
| 6 | **Validación tributaria manual** (SII con fila/captcha) | Tarea manual | Medio |
| 7 | **Baja trazabilidad** por multicanalidad (correo/WhatsApp) en solicitudes | Riesgo de control | Medio |
| 8 | **Separación fondos propios/terceros** sostenida manualmente | Riesgo contable | Alto |
| 9 | **Aprobación de OC** existe en Manager+ (visa de Patricio antes de emitir) pero **sin matriz formal por monto**; las solicitudes previas se piden por correo a Cecilia | Riesgo de control | Medio |
| 10 | **TXT editado a mano** (fecha de pago) tras descargarlo de Manager+ | Tarea manual / riesgo de error | Medio |
| 11 | **Dos TXT separados** (proveedores y personal) cargados por separado en el banco | Ineficiencia | Bajo-medio |
| 12 | **Múltiples planillas Drive paralelas** (gastos y varios, devengo seguros, control nóminas, listado proveedores, cotizaciones) como sistema de control de facto | Riesgo operativo / dispersión | Alto |
| 13 | **Importador/Exportador de Manager+ subutilizado**: ya se usa para devengos, pero el resto del flujo sigue manual | Oportunidad | — |

## 5. Conclusiones para la migración
El área es viable de migrar a Odoo, pero la calidad del resultado depende de: (a) **limpiar maestros** (proveedores, plan de cuentas, centros de costo) antes de migrar; (b) **sistematizar reglas hoy implícitas** (matriz de aprobaciones, campos críticos, separación de fondos); y (c) **resolver las integraciones** que hoy son manuales (Acepta, Banco de Chile, Webpay, SII). Los quick wins propuestos (Entregable 2) atacan los dolores 1, 5, 6 y 9 de inmediato y dejan activos reutilizables.

## 6. Cobertura documental y pendientes a confirmar en entrevistas
**Procesos ya documentados** (manuales revisados): compras/cotizaciones, creación de proveedores, creación de clientes/socios, ingreso de facturas (con/sin OC, vía Acepta), boletas de honorarios, nóminas de pago (proveedores y personal), rendiciones del equipo, conciliación bancaria, cobranza de cuota social, devengo de cuota social y carga de devengos de seguros.

**Pendientes a confirmar en entrevistas:**
- Volúmenes exactos por proceso y tiempos dedicados.
- Composición del equipo y asignación de responsabilidades (hoy se identifican Patricio Fernández, Cecilia Ramírez, Oriana Romero, Carla Carvajal, entre otros).
- Mecánica precisa de **caja chica** y de **ajustes de cuentas por pagar** (anticipos/NC), referenciados en los manuales pero sin manual propio en el set revisado.
- Detalle del manejo de morosidad y pagos parciales de cuota social.
