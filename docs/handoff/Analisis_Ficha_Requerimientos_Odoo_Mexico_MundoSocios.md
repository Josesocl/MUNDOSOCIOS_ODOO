# Análisis: Ficha de Requerimientos Odoo México — MundoSocios CChC

> **Fecha:** 2026-06-24  
> **Fuente:** `[Mundo Socios] Ficha de Requerimientos.xlsx` (Odoo Technologies SA de CV, AM: Liz Gómez)  
> **Propósito:** Extraer restricciones funcionales (columna F) y documentación (columna G) para evaluar alcance real de Odoo vs. lo que propone Indasoge, y preparar criterios de comparación con Addval.

---

## 1. Restricciones críticas detectadas (columna F)

Odoo México respondió con franqueza sobre las limitaciones nativas. Estos son los puntos que impactan directamente el proyecto:

### 🔴 RESTRICCIONES DURAS (requieren desarrollo o integración externa)

| # | Área | Restricción Odoo México | Impacto en MundoSocios |
|---|------|------------------------|----------------------|
| R1 | **TXT bancario** | Odoo NO genera TXT bancarios de manera nativa. Requiere horas adicionales de configuración y **necesita Odoo.sh** (no Odoo Online). | El archivo TXT Banco de Chile es CRÍTICO (nómina de pagos proveedores + personal). Indasoge lo presupuesta en 40 hrs (Compras), pero Odoo México advierte que es desarrollo + requiere Odoo.sh. **Validar con Indasoge y Addval si esto está incluido y en qué modalidad de hosting.** |
| R2 | **Webpay / PAC / PAT** | Odoo NO se conecta con Webpay ni convenios PAC/PAT de forma nativa. Debe ser vía **Nuvei** u otro proveedor soportado (Adyen, Stripe, Xendit, etc.). | 80% de la recaudación de seguros es PAC/PAT. MundoSocios necesita Toku o similar como intermediario. Indasoge presupuesta 40 hrs para pasarelas. **Confirmar que Indasoge/Addval incluyen la integración Nuvei→Webpay o Toku→Odoo.** |
| R3 | **Buk (RRHH/Nómina)** | Odoo NO tiene integración nativa con Buk. El proceso de RRHH se lleva independiente y se registra contablemente de forma manual con un layout. | Aclara que Buk queda fuera del alcance de Odoo. Solo se integra vía asiento contable manual. **Decisión: ¿se mantiene Buk y se hace carga manual, o se migra a Odoo RRHH?** |
| R4 | **Suscripciones en UF** | Multidivisa permite expresar montos en UF, pero **aparecerá en pesos chilenos** en la interfaz. | La cuota social y primas se calculan en UF. El reajuste funciona, pero la presentación al socio será en CLP. **Evaluar si esto es aceptable para el portal del socio.** |
| R5 | **Conciliación bancaria** | Se necesita el extracto bancario **importado manualmente** en Odoo. No hay conexión directa con bancos chilenos. | Hoy se hace con cartola del Banco de Chile. En Odoo será importación manual del extracto. **No es un bloqueante pero impacta la expectativa de "automatización completa" del ROI de Indasoge.** |
| R6 | **Marketing Social** | Solo funciona con Facebook, Instagram, LinkedIn, Twitter, YouTube. **Posts fijos** (no dinámicos). | Limitación menor pero importante para el equipo de marketing que viene de Zoho Social. |

### 🟡 RESTRICCIONES MODERADAS (funcionalidad nativa con limitaciones)

| # | Área | Nota | Implicancia |
|---|------|------|------------|
| R7 | CRM / Formulario web | Funciona nativamente pero no valida si es socio CChC al ingreso. | La validación RUT contra CChC sigue siendo desarrollo a medida (Indasoge lo tiene en Portal del Socio Inteligente, 100 hrs). |
| R8 | Portal del Socio | Portal de clientes nativo da acceso a facturas, pagos, suscripciones. | Funcionalidad base existe; la personalización para mostrar seguros, cargas, beneficios activos es desarrollo. |
| R9 | Contactos / RUT duplicado | Odoo permite registrar varios contactos con el mismo RUT. | Resuelve el caso SODIMAC/EASY (socios en múltiples cámaras regionales con mismo RUT pero distinto número de socio). |

---

## 2. Mapa de documentación Odoo 19.0 por módulo

Todos los links apuntan a documentación oficial de Odoo 19.0:

### CRM
- Pipeline y oportunidades: https://www.odoo.com/documentation/19.0/applications/sales/crm.html
- Formularios web → leads: https://www.odoo.com/documentation/19.0/applications/sales/crm/acquire_leads/opportunities_form.html
- Adquisición de leads: https://www.odoo.com/documentation/19.0/applications/sales/crm/acquire_leads.html

### Helpdesk
- Tickets y SLA: https://www.odoo.com/documentation/19.0/applications/services/helpdesk.html

### Sitio Web y eCommerce
- Website builder: https://www.odoo.com/documentation/19.0/applications/websites/website.html
- Comercio electrónico: https://www.odoo.com/documentation/19.0/applications/websites/ecommerce.html
- Portal de clientes: https://www.odoo.com/documentation/19.0/applications/general/users/portal.html

### Eventos
- Gestión de eventos: https://www.odoo.com/documentation/19.0/applications/marketing/events.html

### Marketing
- Email Marketing: https://www.odoo.com/documentation/19.0/applications/marketing/email_marketing.html
- Encuestas: https://www.odoo.com/documentation/19.0/applications/marketing/surveys.html
- Marketing Social: https://www.odoo.com/documentation/19.0/applications/marketing/social_marketing.html

### Contabilidad y Finanzas
- Contabilidad general: https://www.odoo.com/documentation/19.0/applications/finance/accounting.html
- Facturación electrónica Chile: https://www.odoo.com/documentation/19.0/applications/finance/accounting/customer_invoices/electronic_invoicing/chile.html
- Seguimiento de pagos: https://www.odoo.com/documentation/19.0/applications/finance/accounting/payments/follow_up.html
- Conciliación bancaria: https://www.odoo.com/documentation/19.0/applications/finance/accounting/bank/reconciliation.html
- Pagos por lote (batch): https://www.odoo.com/documentation/19.0/applications/finance/accounting/payments/batch.html
- Proveedores de pago: https://www.odoo.com/documentation/19.0/applications/finance/payment_providers.html

### Compras
- Módulo de compras: https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/purchase.html
- Cuentas analíticas: https://www.odoo.com/documentation/19.0/applications/finance/accounting/reporting/analytic_accounting.html

### Suscripciones
- Pagos automáticos: https://www.odoo.com/documentation/19.0/applications/sales/subscriptions/automatic_payments.html

### Dashboards
- Tableros: https://www.odoo.com/documentation/19.0/applications/productivity/dashboards/build_and_customize_dashboards.html

### Contactos
- Gestión de contactos: https://www.odoo.com/documentation/19.0/applications/essentials/contacts.html

---

## 3. Cruce con la propuesta de Indasoge (563 UF)

| Módulo Indasoge | Hrs | Lo que dice Odoo MX en col. F | Riesgo |
|-----------------|-----|-------------------------------|--------|
| Contabilidad, CRM, Suscripciones, Compras (Estándar) | 120 | CRM y Contabilidad OK nativo. Suscripciones en UF muestra CLP (R4). | Bajo-medio |
| Eventos, Website, Helpdesk (Estándar) | 40 | Eventos y Helpdesk OK nativo. Website es "nice to have" según MX, Indasoge lo incluye. | Bajo |
| Portal del Socio Inteligente (Desarrollo) | 100 | Portal nativo existe pero NO valida RUT vs CChC. Personalización de seguros/cargas es desarrollo. | Medio — las 100 hrs parecen razonables |
| Motor de Recaudación (Desarrollo) | 80 | Notas de cobro masivas OK nativo. **Pero** PAC/PAT requiere Nuvei/tercero (R2), UF se muestra en CLP (R4). | **Alto** — verificar que las 80 hrs cubren la integración real con pasarela chilena |
| WhatsApp Omnicanal (Desarrollo) | 40 | No mencionado por Odoo MX. | Medio — es desarrollo a medida, sin referencia nativa |
| Pasarelas de Pago (Integración) | 40 | **Odoo NO conecta con Webpay ni PAC/PAT nativo** (R2). Solo Nuvei + proveedores listados. | **Alto** — ¿las 40 hrs alcanzan para Nuvei→Webpay + PAC/PAT + conciliación? |
| TXT Banco Chile | (dentro de Compras) | **Odoo NO genera TXT nativo** (R1). Requiere Odoo.sh. | **Alto** — Indasoge no lo separa como línea; ¿está incluido? ¿en qué modalidad de hosting? |

---

## 4. Preguntas clave para Indasoge, Addval y Odoo México

### Para Indasoge (propuesta vigente, 563 UF):
1. **Hosting:** ¿La propuesta contempla Odoo Online o Odoo.sh? El TXT bancario requiere Odoo.sh según Odoo MX.
2. **Pasarela de pago:** ¿Qué proveedor se usará para Webpay y PAC/PAT? ¿Nuvei? ¿Toku? ¿Las 40 hrs de integración cubren todo el ciclo (cobro + conciliación)?
3. **Motor de recaudación:** ¿Las 80 hrs incluyen la lógica de UF→CLP, emisión masiva, mailing de cobro y separación fondos propios/terceros?
4. **TXT Banco de Chile:** ¿En qué línea está presupuestado el desarrollo del formato TXT? ¿Cuántas horas estima?
5. **Buk:** ¿Está fuera de alcance o se contempla alguna integración?

### Para Addval (propuesta pendiente):
1. **Experiencia Chile:** ¿Han implementado conciliación bancaria con bancos chilenos? ¿TXT Banco de Chile?
2. **Pasarelas:** ¿Tienen experiencia con Toku, Webpay/Nuvei en Odoo?
3. **Suscripciones en UF:** ¿Cómo manejan el reajuste UF y la presentación al socio?
4. **Modelo comercial:** ¿Fee fijo por proyecto o bolsa de horas? ¿Soporte post go-live?
5. **Hosting:** ¿Recomiendan Odoo.sh u on-premise para este caso?

### Para Odoo México (referencia de alcance):
1. **Propuesta económica:** ¿Enviarán cotización? ¿En qué plazo?
2. **Soporte local:** ¿Cómo manejan el soporte técnico desde México para un cliente chileno?
3. **Localización Chile:** ¿El módulo de facturación electrónica Chile (DTE) está incluido en la versión enterprise estándar?

---

## 5. Criterios de comparación entre las 3 propuestas

| Criterio | Peso | Indasoge | Addval | Odoo MX |
|----------|------|----------|--------|---------|
| Experiencia en Chile (localización, bancos, SII) | Alto | ✓ Local | ✓ Local | ✗ México |
| Precio implementación | Alto | 563 UF | Pendiente | Pendiente |
| Cobertura TXT bancario + pasarelas | Crítico | Incluido (verificar) | Pendiente | Advierte que no es nativo |
| Modelo de hosting (Online vs .sh) | Alto | No especificado | Pendiente | Recomienda .sh para TXT |
| Soporte post go-live | Medio | 10 hrs (1 mes) | Pendiente | Pendiente |
| Transparencia en restricciones | Alto | Moderada | Pendiente | Alta (esta ficha) |
| Referencia marca Odoo | Bajo | Partner oficial | Partner oficial | Es Odoo |

---

## 6. Conclusión operativa

La ficha de Odoo México es el mejor insumo de "verdad técnica" que tenemos hasta ahora. Las restricciones R1 (TXT), R2 (Webpay/PAC/PAT) y R3 (Buk) son las más relevantes porque impactan directamente los procesos core de MundoSocios. La propuesta de Indasoge no explicita cómo resuelve R1 y R2, lo que genera un riesgo de scope creep o costos adicionales.

**Recomendación:** Usar esta ficha como benchmark técnico para evaluar las 3 propuestas con criterios homogéneos. Las preguntas de la sección 4 deberían ir a Indasoge antes de firmar, y a Addval como parte de su propuesta.
