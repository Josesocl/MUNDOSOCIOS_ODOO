# Diagramas de flujo — Cobranza Cuota Social y Seguros (v2.0)

**Proyecto:** MundoSocios CChC · **Fecha:** 2026-07-08 · **Versión:** 2.0
Actualizan los diagramas de `FLUJOS DE PROCESO/BP Cobranza Cuota Social y Seguros/` (v1.0) con los cambios de julio 2026: certificado de Socio CChC obligatorio, valores/cuentas de cuota social verificados, UF por seguro, ciclo real de Addval, códigos de comercio Transbank, ciclo anual de morosidad y herramientas puente.
GitHub renderiza estos diagramas automáticamente; las versiones SVG/PNG exportadas están en esta misma carpeta.

---

## 1. Incorporación de nuevo socio + cuota social (v2.0)

```mermaid
flowchart TD
    A([Postulante completa formulario web]) --> B["Adjunta CERTIFICADO de Socio CChC<br/>(obligatorio — portal de la Camara)"]
    B --> C{"Validacion equipo MS:<br/>certificado (RUT, razon social, vigencia)<br/>+ validacion por RUT"}
    C -- "Rechazado /<br/>certificado invalido o vencido" --> D["Correo automatico con motivo<br/>e instrucciones del portal CChC"]
    D --> A
    C -- Aprobado --> E["Envio de enlace de pago Webpay<br/>(vigencia 7 dias habiles)"]
    E -- "Vence sin pago" --> F["Solicitud cancelada<br/>+ aviso al interesado"]
    E -- Paga --> G["Pago confirmado<br/>Persona: 1 UF<br/>Empresa: 3 UF hasta 3 miembros<br/>+1 UF por miembro desde el 4to"]
    G --> H["Creacion de cliente en Manager+"]
    H --> I["Devengo cuota social<br/>Empresa: 1150001 → 3210002 (CSEMP)<br/>Persona: 1150002 → 3210001 (CSPER)<br/>CC contrapartida ADM"]
    I --> J["Ticket de cuota social en Zoho CRM"]
    J --> K["Socio ACTIVO + correo de bienvenida<br/>+ aviso a Atencion Integral"]

    subgraph Casos especiales
        R["Reincorporacion:<br/>paga el año en que vuelve<br/>+ certificado CChC vigente<br/>+ comprobante como evidencia"]
        T["Cambio de empresa / beneficiarios:<br/>traspaso interno via Carla Carvajal<br/>+ certificado CChC de la nueva empresa"]
        Q["Renuncia:<br/>correo de confirmacion del socio<br/>antes de procesar la baja"]
    end
    R -.-> B
    T -.-> C
```

**Cambios vs v1.0:** certificado CChC como paso obligatorio y criterio de rechazo · valores de cuota reales (reemplazan 1,44/0,48 UF) · cuentas cruzadas de persona verificadas · casos de reincorporación, traspaso y renuncia · sale Javiera Valdovinos del flujo (informa Carla; apoya Marcos Ibarra).

---

## 2. Recaudación y cobranza recurrente (v2.0)

```mermaid
flowchart TD
    subgraph DEVENGO
        A["Maestro unico de socios y polizas<br/>(mantenedores consolidados)"] --> B["Generadores de devengos (puente):<br/>Seguros MENSUAL — UF por seguro:<br/>Complementario = UF dia 9<br/>Catastrofico = UF cierre mes anterior<br/>Cuota social ANUAL — 1 de enero"]
        B --> C["Importador Manager+<br/>(22 columnas, valida RUT y cliente<br/>ANTES de importar)"]
    end

    C --> D{Cobro}
    D --> E["PAC — bancos recaudadores<br/>(abono agregado por banco,<br/>reintento automatico)"]
    D --> F["PAT — Transbank 32606164<br/>(cargo en tarjeta, reintento automatico)"]
    D --> G["Webpay Plus 51709929 / Webpay.cl 35997075<br/>QR 38323415 / POS 47630680"]
    D --> H["Transferencias y depositos<br/>(comprobante por correo a Oriana)"]

    E & F --> I{"¿Cargo rechazado?<br/>(monto tope, problema de tarjeta)"}
    I -- Si --> J["Reintento del ciclo →<br/>correo con monto pendiente<br/>y pago alternativo<br/>Cambio de tarjeta: desactivar 1ro;<br/>PAC→cta cte hasta 60 dias"]
    I -- No --> K

    G & H & J --> K["Cierre diario de transacciones"]
    K --> L["Marcos Ibarra envia a Addval<br/>(lunes a viernes)"]
    L --> M["Addval sube a Manager+<br/>plazo maximo 48 horas<br/>y rebaja deuda del socio"]
    M --> N["Actualizacion de estados en Zoho<br/>('cuota al dia' / moroso)"]

    K --> O["Cruzador de pagos (semanal):<br/>cartola Excel + Transbank + maestro<br/>→ borrador de PRECONCILIACION"]
    O --> P["Conciliacion MENSUAL post cierre de mes:<br/>PRECONCILIACION → Manager+<br/>(~78% automatica; PAC N:1 manual)"]

    N --> Q{"Morosidad cuota social<br/>(ciclo anual)"}
    Q --> R["Moroso desde MAYO:<br/>correos y llamadas de cobro"]
    R --> S["1 de JULIO: dos comunicados<br/>(eliminados cuota social /<br/>morosos de seguros)"]
    S --> T["Revision de pagos hasta el dia 7"]
    T -- Pago --> N
    T -- Sin pago --> U["Eliminacion formal del socio"]
    U -. "Reincorporacion:<br/>paga el año en curso" .-> D
```

**Cambios vs v1.0:** devengo desde maestro único con generadores validados al peso (fin del copiado mensual) · UF diferenciada por seguro · canales de cobro con códigos de comercio Transbank confirmados · ciclo real Addval (envío diario L-V por Marcos Ibarra, 48 h) · rechazos/reintentos y cambio de tarjeta · cruzador de pagos como paso semanal · conciliación mensual post cierre con PRECONCILIACIÓN (cartola en PDF y Excel; el TXT es solo la nómina de pagos) · ciclo anual de morosidad y eliminación con reincorporación pagando el año en curso.

---

**Pendientes marcados en el BP:** regla exacta de morosidad de seguros ("9") · cuál UF de cierre (ene/feb/mar) aplica a qué caso de cuota social · vigencia máxima del certificado CChC (propuesta: 30 días).
**Fuente de detalle:** `docs/flujos-proceso/BP_Devengo_Recaudacion_Cobranza_MundoSocios.md` y `BP_Procesos_Experiencia_Atencion_MundoSocios.md`.
