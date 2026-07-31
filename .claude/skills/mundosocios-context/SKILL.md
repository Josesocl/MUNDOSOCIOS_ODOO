---
name: mundosocios-context
description: Contexto del proyecto MundoSocios (CChC) — Odoo. Usar al inicio de cualquier sesión que trabaje en este proyecto, antes de generar o modificar contenido.
---

# Contexto del proyecto MundoSocios (CChC)

**Fuente de verdad:** `00_HANDOFF_Contexto_Proyecto_MundoSocios.md` en la carpeta OneDrive del proyecto (`Documentos OneD IBS/CONSULTORÍA JR JOTTAR/CLIENTES CONSULTORA JRJ/MUNDOSOCIOS ODOO/`). Leerlo completo antes de generar contenido nuevo. Este skill resume lo que no cambia.

## Qué es

Consultoría de JR Jottar (IB Solución) para MundoSocios, programa de la CChC: diagnóstico financiero-contable (SOW 15 h / 45 UF, 4 entregables), automatización puente sobre el stack actual, y preparación de la migración a Odoo Enterprise (~5 meses). Cliente funcional: **Patricio Fernández** (Adm. y Finanzas). GG: **Constanza Daniels**. Recaudación: **Oriana Romero**. Compras: **Cecilia Ramírez**.

## Decisiones vigentes (no re-abrir sin nueva instrucción)

- **2026-07-06: la capa Zoho CRM está FUERA DE ALCANCE** (Build/ y Fases 1-2). Vigente: Fase 0 + 5 herramientas Excel + Validador SII.
- Integración Manager+ **por archivo, no API**. Verificación SII: **SimpleAPI (simpleapi.cl)** desde 2026-07-31 — key en env `SIMPLEAPI_API_KEY` (NUNCA en código/docs), cuota API RUT 10/mes solo para altas de proveedores, cliente con caché y control de cuota en `herramientas/sii-simpleapi/`. Endpoint confirmado: `GET https://rut.simpleapi.cl/v2/{rut}`, header `Authorization` con la key directa; el resto de las APIs (DTE/RCV/BHE) usan otros hosts — ver README de la carpeta. API Gateway y BaseAPI quedan como legado.
- El dominio `cchc.cl` no es accesible; parametrizar owners, nunca cuentas del consultor.

## Reglas de negocio fijas (verificadas contra archivos productivos 2026-07-07)

- **Matriz de aprobaciones (CLP bruto c/IVA):** ≤500.000 dueño de presupuesto · 500.001–1.000.000 Cecilia Ramírez · 1.000.001–5.000.000 Patricio Fernández · >5.000.000 doble firma Patricio + Constanza.
- **Cuota social (anual, devengo único al 1 de enero):** Persona **1 UF** (DEBE 1150002 / HABER 3210001, doc CSPER) · Empresa **3 UF hasta 3 miembros + 1 UF por miembro desde el 4º** (DEBE 1150001 / HABER 3210002, doc CSEMP). CC contrapartida ADM. Glosa detalle `{RUT} CE|CP {AA} {CÁMARA}`. **Los documentos antiguos que dicen 1,44/0,48 UF están desactualizados.**
- **Seguros (fondos de terceros, devengo mensual):** Plan Socios 1130004/3310005/PSOC · Complementario 1130003/3310003/SCOMP (UF del día 9) · Catastrófico 1130002/3310001/SCAT (UF del último día del mes anterior) · Plan Carreño 1130005/3310004/PCARR. CC contrapartida MS; Conceptos 1/2 = `99999`/`500` en todas las filas. Prima = factor UF × UF del seguro. Cada seguro usa su propia UF.
- **Addval:** Marcos Ibarra envía el cierre diario (L-V); Addval tiene 48 h para subirlo a Manager+.
- Banco de Chile cta. 8001104309; nóminas todos los martes; retención boletas honorarios 13,75%. **La cartola se descarga en PDF y Excel; el TXT es solo el archivo de nómina de pagos que se carga al banco.** Javiera Valdovinos ya no está en MundoSocios.
- **Códigos de comercio Transbank:** 32606164 PAT · 51709929 Webpay Plus · 35997075 Webpay.cl · 38323415 Cobro QR · 47630680 Máquina POS · 35171665 máquina móvil (inactivo).

## Gotchas técnicos (aprendidos con costo)

- **openpyxl + Excel en español:** `XLOOKUP` escrito por openpyxl produce `#NAME?` (falta prefijo `_xlfn.`) — usar `INDEX/MATCH`. `TEXTJOIN` → usar `&`. **Siempre verificar fórmulas con recálculo real** (LibreOffice headless → leer con `data_only=True`); que openpyxl guarde sin error no basta.
- RUTs con dígito K: **K mayúscula** en archivos de importación Manager+.
- Archivos de devengo: 22 columnas A–V, contrapartida en la última fila (cuenta ingreso, CC `MS`, total en HABER). Generador: `herramientas/generador-devengos/`.

## Estilo de trabajo del consultor

Respuestas cortas y directas, sin relleno, sin emojis, sin documentación innecesaria salvo que se pida.

## Este repositorio

`EVALUACION_PROYECTO_2026-07-07.md` (evaluación completa + 16 mejoras) · `docs/` (especificación suscripciones Odoo, política de morosidad, BP proveedor corregido, correcciones pendientes de OneDrive) · `herramientas/generador-devengos/` (generador de devengos de seguros para Manager+, con tests).
