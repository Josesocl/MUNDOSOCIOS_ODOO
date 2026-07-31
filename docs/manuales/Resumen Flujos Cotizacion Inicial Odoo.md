> **Nota de migración (2026-07-31):** en OneDrive este contenido existe dos veces con nombres distintos e idéntico texto: `Resumen Flujos Cotización Inicial Odoo.md` y `Resumen FLUJOS PROCESOS MS Proy Odoo.md` (carpeta `FLUJOS DE PROCESO/BP Procesos/`). Se migra una sola copia. Las imágenes `media/image1..5.png` referenciadas son los diagramas del documento Word original y no se migran.

**Resumen Flujos Cotización Inicial**

**Implementación Odoo**

**Objetivo de la Implementación (Alcance Inicial)**

Implementar Odoo (CRM/Contabilidad/Sitio Web/Herramientas de
MKT/Tableros/Recaudación/Inscripciones y comprar tickets para
actividades), reemplazando:

- Zoho One: CRM/Herramientas de MKT (Campaigns/Survey/Social)

- Contabilidad hoy en Manager+

- Plataformas Web

Incorporar:

- Plataforma de recaudación

- Portal del Socio

**Módulos Contabilidad y Recaudación**

**Flujo Compras**![](media/image1.png){width="6.1375in"
height="2.7805555555555554in"}

 **Solicitud de Compra**

- Área requirente completa formulario de orden de compra.

- Se registra la necesidad y datos básicos del gasto. (Centro de
  Costo/Línea de negocio/proyecto y cuenta contable)

 **Confección y Envío de Orden de Compra**

- Administración genera la OC.

- Se activa flujo de aprobación.

- La OC se envía automáticamente al proveedor.

 **Recepción de Factura**

- Se recibe la factura del proveedor.

- Se registra en el ERP y se asocia a la OC (Proceso automático de
  acuerdo con registro OC)

 **Ingreso Contable:** Se genera la cuenta por pagar correspondiente.

 **Validación de Entrega**: recepción conforme del bien o servicio.

 **Respaldo Documental:** Se adjuntan y resguardan OC, factura y
recepción.

 **Nómina de Pago**

- Se prepara la nómina de pagos.

- Se genera archivo bancario (TXT) y envía directamente al Banco Chile.

 **Aprobaciones:** se revisa y carga el pago en el banco, aprobación
apoderados.

 **Pago al Proveedor**

- Banco ejecuta el abono.

- Se registra y concilia el pago en el sistema.

 **Conciliación Bancaria**

- Conciliar pagos ejecutados vs extracto bancario

- Identificar diferencias (monto / fecha)

- Cerrar cuentas por pagar correctamente

**Flujo Recaudación y Cobranza**

![](media/image2.png){width="4.845138888888889in"
height="3.0970286526684165in"}

Otras aclaraciones del proceso:

 **Maestros y estructura base**

- Socios, beneficios/seguros, copagos, centros de costo, cuentas
  contables.

- Enfoque en separación de fondos propios vs terceros.

 **Generación de Notas de Cobro (no facturas)**

- Emisión mensual masiva (\~1.500).

- Generación automática de envío de mailings de cobro

- Documento interno sin SII.

- Genera asiento contable automático.

 **Recaudación y registro de pagos**

- Transferencias y pagos recurrentes.

- Asociación pago--socio--período.

- Manejo de pagos parciales y morosidad.

 **Conciliación bancaria**

- Alto volumen.

- Reglas automáticas y manejo de excepciones.

- Punto crítico del proceso.

 **Reportes clave**

- Recaudación por período, seguro y socio.

- Morosidad.

- Fondos recaudados vs pagos a aseguradoras.

- Reportes contables y de auditoría.

- Mailings enviados, aperturas, respuestas, conversión apago.

**Integraciones (a evaluar en la cotización), a nivel referencial:**

- Integración con Buk

- Integración con plataformas de pago recurrente (ej. Toku)

- Migración de datos básicos desde sistemas actuales

- Portal del socio

\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

**ÁREA DE EXPERIENCIA DE SOCIOS**

Sistemas y plataformas que interactúan:

1.  Zoho: CRM, Project, Survey, Campaign.

2.  WordPress:\
    - Página web (solo informativa)\
    - Plataforma de experiencias: donde se crean todas las actividades
    para que los socios se inscriban.

3.  Webpay: para el pago de las actividades en la plataforma de
    experiencias

4.  Hoja de cálculos de Google: donde van quedando registrados
    automáticamente todos los inscritos por cada actividad.

5.  Ecosistema Microsoft: Onedrive, Outlook, Teams.

6.  Redes sociales: WhatsApp, Instagram, LinkedIn

7.  Planillas de Excel individuales

El socio:

1.  Puede tener más de un seguro de salud contratado, para él y/o sus
    cargas.

2.  Puede haberse inscrito en múltiples actividades en un período de
    tiempo

No tiene un portal dónde poder ver su estado de pago de la cuota social,
todos sus seguros contratados, su historial de actividades, los
beneficios activos que tiene, etc.

**Flujo incorporación nuevos socios Mundo Socios**

![](media/image3.png){width="4.598464566929134in"
height="3.055757874015748in"}

Consideraciones:

- Existen 2 vías por las que el Socio envía formulario de incorporación:

  - Contacto con Embajador u otro Socio que le cuenta que es MundoSocios
    y decide participar

  - Contacto con área de Atención Integral al Socio, quienes explican
    qué es MundoSocios, beneficios, actividades

- Tiempos de respuesta: Manejamos tiempos de respuesta de 24 hrs entre
  recepcionado el formulario de incorporación y el acuse de recibo al
  Socio con su solicitud.

- Encargada de las incorporaciones es Carla Carvajal. En su ausencia,
  formularios son redirigidos a quien se acuerde su reemplazo.

- El formulario web no está integrado al CRM, por lo que se traspasa la
  información manualmente. El formulario web no discrimina entre uno
  socio CChC y una persona que no es parte de la cámara, por lo que, en
  estricto rigor, cualquier persona podría completar el formulario.

**Flujo de gestión de solicitudes de socios (generales)**

![](media/image4.png){width="4.9047878390201225in"
height="3.244329615048119in"}

Comentarios:

- El flujo tiene baja trazabilidad por la multicanalidad, por lo que no
  tenemos cómo saber los estados de las solicitudes (Ej: abiertas, en
  proceso, cerradas) y genera dependencia de quién recibe la solicitud.

- Hay un registro incompleto en el CRM, ya que todo lo que entra por
  WhatsApp, teléfono o presencial depende de registro manual. Eso genera
  un alto riesgo de que casos nunca queden en el sistema.

- El socio no sabe en qué está su solicitud (no recibe un n° de atención
  / ticket / etc).

**Flujo gestión de actividades y experiencias**

![](media/image5.png){width="6.1375in" height="3.9875in"}

Consideraciones:

- La plataforma de experiencias (WordPress) no está integrada al CRM,
  por lo que el socio/a cada vez que quiere inscribirse en una
  actividad, debe volver a ingresar todos sus datos personales. De la
  misma manera, al no estar integradas, se debe cargar manualmente al
  CRM el listado de participantes de cada actividad.

- Cada actividad puede tener distintos requerimientos. Cada nuevo
  requerimiento (Ej: incorporar un campo adicional de información) ha
  conllevado un desarrollo desde Meat.
