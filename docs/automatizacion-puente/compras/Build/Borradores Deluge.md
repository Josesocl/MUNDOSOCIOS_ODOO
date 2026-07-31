# Desarrollo Deluge — Zoho CRM

**Versión:** 2.0 · **Fecha:** 2026-07-02 (reemplaza v1.0 del 2026-06-18)
**Cambios v2.0:** desarrollo concreto de `validarSII` (endpoint real investigado) y del sync con Manager+ (`exportarProveedorManager` ahora con los campos reales de Manager+, separado en Proveedor/Contacto/Cuenta Bancaria, más `exportarOCManager`).

> **Actualización 2026-07-31 (al migrar este documento al repositorio):** el proveedor de verificación SII definitivo es **SimpleAPI** (`GET https://rut.simpleapi.cl/v2/{rut}`, header `Authorization` con la key directa), no BaseAPI ni API Gateway — ver `herramientas/sii-simpleapi/README.md`. Las referencias a BaseAPI en §2 y §5 quedan como estaban por fidelidad histórica; si `validarSII` se llega a implementar, usar el endpoint y esquema de respuesta de SimpleAPI (cuota: 10 consultas RUT/mes — consultar solo al crear/editar proveedor).

Crear en `Setup → Automation → Functions`. Nombres de módulos/campos según `Especificacion modulos Zoho CRM.md` (v2, 2026-07-02).
Convención: endpoints y credenciales **siempre** en variables de organización (`Setup → Developer Space → Variables`), nunca hardcodeadas en el código.

**⚠️ Nota general importante:** este código no se puede ejecutar ni probar fuera de una cuenta Zoho real (Deluge es un lenguaje propietario de Zoho, sin intérprete externo). Está escrito con el mayor cuidado posible siguiendo la sintaxis documentada de Deluge, pero **debe probarse en un entorno sandbox/desarrollo de Zoho antes de activarlo en producción**, igual que se haría con cualquier desarrollo nuevo.

---

## 1. `resolverAprobador` — ruteo por tramo + dueño de presupuesto
**Actualizado 2026-07-02:** ahora escribe **2 pares** de campos (Aprobador/Resultado 1 y 2), no uno solo — necesario para que el Approval Process de Zoho pueda armarse con 2 niveles reales que se disparan en secuencia cuando el tramo exige doble firma.

Dispara al pasar la OC a "En aprobación". Lee `Parametros_Aprobacion`, resuelve "dueño del presupuesto" por centro de costo y escribe los campos de aprobador.

```
void resolverAprobador(String ocId)
{
    oc = zoho.crm.getRecordById("Ordenes_Compra", ocId.toLong());
    monto = ifnull(oc.get("Monto_bruto_c_IVA"), 0).toDecimal();
    centroCosto = ifnull(oc.get("Centro_de_costo"), "");

    criterio = "(Activo:equals:true)";
    tramos = zoho.crm.searchRecords("Parametros_Aprobacion", criterio);
    aprobador1 = null;
    aprobador2 = null;
    for each t in tramos
    {
        desde = ifnull(t.get("Monto_desde"), 0).toDecimal();
        hastaRaw = t.get("Monto_hasta");
        hasta = if(hastaRaw == null, 999999999999, hastaRaw.toDecimal());
        if(monto >= desde && monto <= hasta)
        {
            aprobador1 = t.get("Aprobador_1");
            aprobador2 = t.get("Aprobador_2");
        }
    }

    if(aprobador1 == null)
    {
        duenos = Map();
        duenos.put("Experiencias", "rel.comercial@mundosocios");  // ejemplo, reemplazar
        // ...completar con los centros de costo reales
        aprobador1 = duenos.get(centroCosto);
    }

    update = Map();
    update.put("Aprobador_asignado_1", aprobador1);
    update.put("Resultado_aprobacion_1", "Pendiente");
    if(aprobador2 != null)
    {
        // tramo con doble firma (sobre $5.000.000)
        update.put("Aprobador_asignado_2", aprobador2);
        update.put("Resultado_aprobacion_2", "Pendiente");
    }
    else
    {
        update.put("Aprobador_asignado_2", null);
        update.put("Resultado_aprobacion_2", "No aplica");
    }
    update.put("Fecha_entrada_aprobacion", zoho.currenttime);
    zoho.crm.updateRecord("Ordenes_Compra", ocId.toLong(), update);
}
```

> El **Approval Process** de Zoho hace el envío y la captura de la decisión, configurado con 2 niveles secuenciales: Nivel 1 = `Aprobador_asignado_1`, Nivel 2 = `Aprobador_asignado_2` (se salta solo si el campo viene vacío — comportamiento nativo de Zoho cuando el aprobador de un nivel es nulo). El Approval Process, al aprobar/rechazar cada nivel, debe tener configurada la acción "Update Field" para escribir `Resultado_aprobacion_1`/`Resultado_aprobacion_2` — ver detalle en `Blueprint - Proceso Compras y Proveedores.md`.

---

## 2. Validador SII — `validarSII` + `actualizarVerificacionSII`

### 2.1 Qué API se usa y por qué
El sitio oficial del SII (`www2.sii.cl/stc/noauthz`) tiene fila de espera y captcha: no se puede invocar desde una función automatizada. Se usa en su lugar **BaseAPI** (`baseapi.cl`), que expone la misma información pública del contribuyente por REST.

**Investigado (no probado en vivo — el sitio bloquea el acceso automatizado a su documentación desde esta sesión, así que estos datos vienen de la información pública indexada de BaseAPI y deben confirmarse contra su documentación real al contratar):**

| Dato | Valor |
|---|---|
| Endpoint | `https://api.baseapi.cl/api/v1/sii/contribuyente` |
| Método | `POST` |
| Autenticación | Header `x-api-key` |
| Body (a confirmar exacto) | `{"rut": "76123456-7"}` |
| Campos de respuesta esperados | `rut`, `razonSocial`, `situacionTributaria` (valores observados: `"Activo"`, `"Sin inicio de actividades"`, término de giro), `inicioActividades`, `regimenTributario`, `giros` (arreglo de `{codigo, descripcion, tipo}`) |

**Antes de activar en producción:**
1. Contratar BaseAPI (o alternativa API Gateway `apigateway.cl`) y obtener el `x-api-key` real.
2. Hacer una llamada de prueba real (Postman/curl) con un RUT conocido y **confirmar los nombres exactos de los campos** contra la respuesta real — el mapeo de abajo puede necesitar ajustes menores.
3. Confirmar el costo por consulta/mes y quién lo aprueba (Patricio/Constanza).

### 2.2 `validarSII` — llamada a la API, devuelve un Map
A diferencia del borrador v1.0 (que solo devolvía la situación tributaria), esta versión trae **también** Razón Social y Giro, para poder automatizar la comparación completa que hoy se hace a mano en la Ficha de Proveedores (Excel).

```
Map validarSII(String rut)
{
    resultado = Map();
    resultado.put("situacion", "Pendiente");
    resultado.put("razonSocial", "");
    resultado.put("giro", "");
    resultado.put("error", "");

    endpoint = zoho.crm.getOrgVariable("sii_endpoint");   // https://api.baseapi.cl/api/v1/sii/contribuyente
    apiKey = zoho.crm.getOrgVariable("sii_api_key");
    rutLimpio = rut.replaceAll("[^0-9kK]", "").toUpperCase(); // sin puntos ni guion, con DV

    if(endpoint == null || apiKey == null || endpoint == "" || apiKey == "")
    {
        resultado.put("error", "Falta configurar sii_endpoint / sii_api_key en variables de organizacion");
        return resultado;
    }

    try
    {
        body = Map();
        body.put("rut", rutLimpio);

        respuesta = invokeurl
        [
            url: endpoint
            type: POST
            parameters: body.toString()
            headers: {"x-api-key": apiKey, "Content-Type": "application/json", "Accept": "application/json"}
        ];

        situacionRaw = ifnull(respuesta.get("situacionTributaria"), "").toUpperCase();
        if(situacionRaw == "ACTIVO")
        {
            resultado.put("situacion", "Vigente");
        }
        else if(situacionRaw != "")
        {
            resultado.put("situacion", "No vigente");
        }
        // si situacionRaw viene vacio, queda "Pendiente" (respuesta inesperada o RUT no encontrado)

        resultado.put("razonSocial", ifnull(respuesta.get("razonSocial"), ""));

        giros = ifnull(respuesta.get("giros"), List());
        girosTexto = "";
        for each g in giros
        {
            desc = ifnull(g.get("descripcion"), "");
            if(desc != "")
            {
                girosTexto = if(girosTexto == "", desc, girosTexto + ", " + desc);
            }
        }
        resultado.put("giro", girosTexto);
    }
    catch (e)
    {
        resultado.put("error", "Error consultando SII: " + e.toString());
    }

    return resultado;
}
```

### 2.3 `actualizarVerificacionSII` — orquesta la llamada y escribe el registro
Dispara al crear/editar un `Proveedor` (workflow rule: "on create or edit"). Llama a `validarSII`, escribe los campos SII, calcula las 4 comparaciones (mismo criterio que la Ficha_Proveedor en Excel: comparación insensible a mayúsculas y espacios) y recalcula `Estado proveedor`.

```
void actualizarVerificacionSII(String provId)
{
    p = zoho.crm.getRecordById("Proveedores", provId.toLong());
    rut = ifnull(p.get("RUT"), "");
    if(rut == "")
    {
        return;
    }

    sii = validarSII(rut);
    if(sii.get("error") != "")
    {
        // no se pudo consultar: no se bloquea el registro, queda para revision manual (Fase 1)
        info sii.get("error");
        return;
    }

    razonIngresada = ifnull(p.get("Razon_social"), "").trim().toUpperCase();
    razonSii = ifnull(sii.get("razonSocial"), "").trim().toUpperCase();
    coincideRazon = if(razonIngresada == "" || razonSii == "", "Pendiente", if(razonIngresada == razonSii, "Si", "No"));

    giroIngresado = ifnull(p.get("Giro"), "").trim().toUpperCase();
    giroSii = ifnull(sii.get("giro"), "").trim().toUpperCase();
    // el giro de la SII puede traer varias actividades separadas por ", " -> basta con que el giro
    // ingresado aparezca como substring de alguna de ellas
    coincideGiro = if(giroIngresado == "" || giroSii == "", "Pendiente", if(giroSii.contains(giroIngresado), "Si", "No"));

    update = Map();
    update.put("Situacion_SII", sii.get("situacion"));
    update.put("Razon_Social_SII", sii.get("razonSocial"));
    update.put("Giro_SII", sii.get("giro"));
    update.put("Coincide_Razon_Social", coincideRazon);
    update.put("Coincide_Giro", coincideGiro);

    // Estado proveedor: igual regla que la Ficha_Proveedor en Excel.
    // Direccion y DTE no se verifican por esta API (BaseAPI /contribuyente no trae direccion ni
    // documentos DTE autorizados) - esas 2 verificaciones siguen siendo manuales (Fase 1) por ahora.
    bancoOk = ifnull(p.get("Banco"), "") != "" && ifnull(p.get("Tipo_de_cuenta"), "") != "" &&
              ifnull(p.get("N_cuenta"), "") != "" && ifnull(p.get("Email_pago"), "") != "";
    coincideDireccion = ifnull(p.get("Coincide_Direccion"), "Pendiente");
    coincideDte = ifnull(p.get("Coincide_DTE"), "Pendiente");

    if(sii.get("situacion") == "Vigente" && bancoOk && coincideRazon == "Si" && coincideGiro == "Si"
       && coincideDireccion == "Si" && coincideDte == "Si")
    {
        update.put("Estado_proveedor", "Apto");
    }
    else
    {
        update.put("Estado_proveedor", "En validacion");
    }

    zoho.crm.updateRecord("Proveedores", provId.toLong(), update);
}
```

> **Importante — alcance real de la automatización:** BaseAPI `/contribuyente` (según lo investigado) **no entrega dirección ni documentos DTE autorizados** — solo razón social, giro y situación tributaria. Por eso `Coincide_Direccion` y `Coincide_DTE` siguen siendo **manuales** (igual que en la Ficha_Proveedor de Excel) incluso con esta automatización activa. Si se necesita automatizar también esas dos, hay que confirmar si algún otro endpoint de BaseAPI/API Gateway las entrega (dirección tributaria sí suele estar disponible en otros endpoints de "contribuyente ampliado"; documentos DTE autorizados normalmente requiere el endpoint de "autorización de folios/DTE", otro servicio del mismo proveedor).

---

## 3. Sync con Manager+ (archivo para carga manual)

### 3.1 Cómo funciona el "sync"
Manager+ no tiene API — el intercambio es siempre por archivo. El flujo real es:
1. Zoho genera el archivo (esta sección).
2. Una persona lo descarga y lo importa manualmente en Manager+ (Mantenedores → Importador de datos, o el flujo de creación de proveedor/OC que corresponda).
3. Una vez creado en Manager+, la persona vuelve a Zoho y completa el campo `N° OC Manager` (o el ID de proveedor que corresponda) a mano — este paso de vuelta **no se automatiza** porque no hay forma de leer Manager+ desde Zoho.

### 3.2 `exportarProveedorManager` — usa los campos reales de la pantalla de Manager+
A diferencia del borrador v1.0 (que inventaba columnas genéricas), esta versión usa los **campos reales** de la pantalla "Crear Cliente/Proveedor" de Manager+ (`Manual creacion de proveedores`, relevado en el diagnóstico), separados en sus 3 secciones reales: **Proveedor**, **Contacto** (representante legal) y **Cuenta bancaria** — porque así están separados en Manager+ también.

```
void exportarProveedorManager(String provId)
{
    p = zoho.crm.getRecordById("Proveedores", provId.toLong());
    rut = ifnull(p.get("RUT"), "");

    // --- Archivo 1: Proveedor (pestaña "Cliente/Proveedor" en Manager+) ---
    cabProv = "RUT;Razon_social;Nombre_de_fantasia;Giro;Correo_electronico_SII;Correo_electronico_comercial;"
            + "Tipo_Proveedor;Descripcion_de_direccion;Direccion;Comuna;Ciudad;Region;Pais;Telefono";
    filaProv = rut + ";" + ifnull(p.get("Razon_social"), "") + ";" + ifnull(p.get("Nombre_de_fantasia"), "") + ";"
             + ifnull(p.get("Giro"), "") + ";" + ifnull(p.get("Correo"), "") + ";" + ifnull(p.get("Correo"), "") + ";"
             + "Nacional" + ";" + "Direccion Principal" + ";" + ifnull(p.get("Direccion"), "") + ";"
             + ifnull(p.get("Comuna"), "") + ";" + ifnull(p.get("Ciudad"), "") + ";" + ifnull(p.get("Region"), "") + ";"
             + ifnull(p.get("Pais"), "Chile") + ";" + ifnull(p.get("Telefono"), "");
    archivoProv = (cabProv + "\n" + filaProv).toFile("proveedor_" + rut + ".csv");

    // --- Archivo 2: Contactos (pestaña "Contactos" en Manager+) — hasta 2 representantes legales ---
    cabCont = "RUT_Proveedor;Nombres;Cargo;Correo_electronico;Telefono;Contacto_principal";
    filasCont = List();
    if(ifnull(p.get("Rep1_Nombre"), "") != "")
    {
        filasCont.add(rut + ";" + p.get("Rep1_Nombre") + ";Representante Legal;" + ifnull(p.get("Rep1_Correo"), "") + ";"
                    + ifnull(p.get("Rep1_Telefono"), "") + ";Si");
    }
    if(ifnull(p.get("Rep2_Nombre"), "") != "")
    {
        filasCont.add(rut + ";" + p.get("Rep2_Nombre") + ";Representante Legal;" + ifnull(p.get("Rep2_Correo"), "") + ";"
                    + ifnull(p.get("Rep2_Telefono"), "") + ";No");
    }
    contenidoCont = cabCont;
    for each fc in filasCont
    {
        contenidoCont = contenidoCont + "\n" + fc;
    }
    archivoCont = contenidoCont.toFile("proveedor_" + rut + "_contactos.csv");

    // --- Archivo 3: Cuenta bancaria (pestaña "Cuentas bancarias" en Manager+) ---
    cabCta = "RUT_Proveedor;Tipo_Cuenta_Bancaria;Numero_Cuenta_Bancaria;Banco_Cuenta_Bancaria;Cuenta_por_defecto";
    filaCta = rut + ";" + ifnull(p.get("Tipo_de_cuenta"), "") + ";" + ifnull(p.get("N_cuenta"), "") + ";"
            + ifnull(p.get("Banco"), "") + ";Si";
    archivoCta = (cabCta + "\n" + filaCta).toFile("proveedor_" + rut + "_cuenta_bancaria.csv");

    // Adjuntar los 3 archivos al registro del proveedor para que quien haga el ingreso en Manager+
    // los tenga a mano (Manager+ no acepta un unico archivo combinado porque son 3 pantallas distintas)
    zoho.crm.attachFile("Proveedores", provId.toLong(), archivoProv);
    zoho.crm.attachFile("Proveedores", provId.toLong(), archivoCont);
    zoho.crm.attachFile("Proveedores", provId.toLong(), archivoCta);
}
```

> **Pendiente de confirmar con Patricio (Task 2.0 del plan de implementación):** si el "Importador de datos" de Manager+ tiene un tipo de importación para **crear proveedores completos** (como sí lo tiene para "Comprobantes contables con documento", usado hoy para los devengos de seguros). Si NO lo tiene, estos 3 archivos igual sirven como **ficha de referencia rápida para digitar** en las 3 pestañas de Manager+ — más rápido que ir a buscar cada dato a Zoho, aunque no sea una carga masiva real.

### 3.3 `exportarOCManager` — archivo de OC para Manager+
*(sin cambios de fondo respecto a v1.0; se ajustan los nombres de campo al RUT del proveedor real)*

```
void exportarOCManager(String ocId)
{
    oc = zoho.crm.getRecordById("Ordenes_Compra", ocId.toLong());
    proveedorRut = ifnull(oc.get("Proveedor.RUT"), "");
    cab = "Proveedor_RUT;Monto_bruto;Centro_de_costo;Cuenta_contable;Detalle";
    fila = proveedorRut + ";" + ifnull(oc.get("Monto_bruto_c_IVA"), 0) + ";" +
           ifnull(oc.get("Centro_de_costo"), "") + ";" + ifnull(oc.get("Cuenta_contable"), "") + ";" +
           ifnull(oc.get("Solicitud.Descripcion"), "");
    contenido = cab + "\n" + fila;
    archivo = contenido.toFile("oc_" + ocId + ".csv");
    zoho.crm.attachFile("Ordenes_Compra", ocId.toLong(), archivo);
}
```

> Los **layouts exactos** (columnas, separador, encoding) de los 3 puntos anteriores dependen de lo que Manager+ acepte realmente — esto sigue siendo la **Task 2.0** pendiente del plan de implementación, ahora con mayor detalle sobre qué preguntar exactamente (¿existe import de proveedor/contacto/cuenta bancaria, o solo de comprobantes contables?).

---

## 4. `validarPresupuesto` — alerta de presupuesto excedido (Task 2.5)
Dispara **junto con** `resolverAprobador`, al crear la `Orden de Compra` (mismo Workflow Rule "on create", las dos funciones en secuencia — ver `Workflow Rules - Alertas y Recordatorios.md`). Es informativa: **no bloquea** el flujo, solo marca `Excede_presupuesto` y notifica.

```
void validarPresupuesto(String ocId)
{
    oc = zoho.crm.getRecordById("Ordenes_Compra", ocId.toLong());
    centroCosto = ifnull(oc.get("Centro_de_costo"), "");
    montoOc = ifnull(oc.get("Monto_bruto_c_IVA"), 0).toDecimal();
    if(centroCosto == "")
    {
        return;
    }

    // Periodo = mes-anio de creacion de la OC, formato "2026-07".
    // Nota: .toString(patron) sobre un DateTime es sintaxis documentada de Deluge para formatear
    // fechas, pero conviene confirmar el patron exacto ("yyyy-MM") en sandbox antes de depender de el.
    periodo = oc.get("Created_Time").toString("yyyy-MM");

    // 1) presupuesto asignado para ese centro + periodo
    criterioPpto = "(Centro_de_costo:equals:" + centroCosto + ") and (Periodo:equals:" + periodo + ") and (Activo:equals:true)";
    presupuestos = zoho.crm.searchRecords("Presupuestos", criterioPpto);
    if(presupuestos.size() == 0)
    {
        return; // sin presupuesto cargado para ese centro+periodo: no se puede validar, no se bloquea
    }
    montoAsignado = ifnull(presupuestos.get(0).get("Monto_asignado"), 0).toDecimal();

    // 2) comprometido: todas las OC del mismo centro, filtrando el mismo periodo en Deluge
    //    (el criterio de busqueda de Zoho no compara "mismo mes" directamente sobre un campo fecha)
    criterioOC = "(Centro_de_costo:equals:" + centroCosto + ")";
    ocsDelCentro = zoho.crm.searchRecords("Ordenes_Compra", criterioOC);
    comprometido = 0.0;
    for each o in ocsDelCentro
    {
        estadoO = ifnull(o.get("Estado"), "");
        periodoO = o.get("Created_Time").toString("yyyy-MM");
        if(periodoO == periodo && estadoO != "Rechazada")
        {
            comprometido = comprometido + ifnull(o.get("Monto_bruto_c_IVA"), 0).toDecimal();
        }
    }

    excede = comprometido > montoAsignado;
    update = Map();
    update.put("Excede_presupuesto", excede);
    zoho.crm.updateRecord("Ordenes_Compra", ocId.toLong(), update);

    if(excede)
    {
        disponibleAntes = montoAsignado - (comprometido - montoOc);
        mensaje = "La Orden de Compra de " + centroCosto + " (periodo " + periodo + ") hace que el gasto "
                + "comprometido ($" + comprometido + ") supere el presupuesto asignado ($" + montoAsignado + "). "
                + "Disponible antes de esta OC: $" + disponibleAntes + ".";
        destinatario = zoho.crm.getOrgVariable("presupuesto_alerta_email"); // ej. Patricio, o el dueño del centro
        sendmail
        [
            from: zoho.adminuserid
            to: destinatario
            subject: "Alerta de presupuesto excedido - " + centroCosto + " " + periodo
            message: mensaje
        ];
    }
}
```

> **Pendiente de decisión:** ¿quién carga y mantiene el módulo `Presupuestos` cada mes? Es la pieza manual que sostiene esta alerta — sin presupuesto cargado para un centro+período, la función simplemente no valida nada (no bloquea, pero tampoco alerta).

---

## 5. Variables de organización a crear antes de activar

| Variable | Valor | Dónde se usa |
|---|---|---|
| `sii_endpoint` | `https://api.baseapi.cl/api/v1/sii/contribuyente` (confirmar al contratar) | `validarSII` |
| `sii_api_key` | La `x-api-key` que entregue BaseAPI (o el token de API Gateway si se elige esa alternativa) | `validarSII` |
| `presupuesto_alerta_email` | Correo(s) que reciben la alerta de presupuesto excedido (ej. Patricio) | `validarPresupuesto` |

## 6. Checklist antes de pasar a producción
- [ ] Contratar BaseAPI o API Gateway y obtener credenciales reales.
- [ ] Probar `validarSII` con 3-5 RUT conocidos (uno vigente, uno sin inicio de actividades, uno inexistente) y ajustar el mapeo de campos si la respuesta real difiere de lo investigado.
- [ ] Confirmar con Patricio si Manager+ soporta import de proveedor/contacto/cuenta bancaria o si estos archivos son solo de apoyo para digitación manual.
- [ ] Decidir si se automatiza también la verificación de Dirección y Documentos DTE (requeriría otro endpoint del mismo proveedor de API u otra fuente).
- [ ] Probar `resolverAprobador` y `exportarOCManager` con casos reales de cada tramo de aprobación.
- [ ] Confirmar el patrón de formato de fecha (`.toString("yyyy-MM")`) en sandbox — usado por `validarPresupuesto` para calcular el período.
- [ ] Definir con Patricio quién carga mensualmente el módulo `Presupuestos` (sin esto, la alerta de presupuesto no tiene con qué comparar).
- [ ] Probar `validarPresupuesto` con un centro de costo cargado a propósito por debajo del comprometido, para confirmar que llega la alerta.
