# Política de morosidad y pagos parciales — BORRADOR para validación

**Proyecto:** MundoSocios CChC · **Fecha:** 2026-07-07 · **Estado:** propuesta del consultor — requiere decisión de Constanza Daniels (GG) y Oriana Romero (Recaudación); cierra las decisiones pendientes **DP-04 y DP-06** del Blueprint de Recaudación y el punto crítico **PC-08** ("no hay proceso de morosidad ni pagos parciales sistematizado").

Aplica desde ya (proceso manual/Zoho) y queda parametrizada en Odoo (Follow-up) al migrar.

---

## 1. Escalamiento de cobranza (propuesta)

| Días desde vencimiento | Acción | Canal | Responsable |
|---|---|---|---|
| 0 | Nota de cobro emitida con enlace de pago | Correo | Sistema |
| +7 | Recordatorio amable con enlace de pago | Correo | Sistema |
| +15 | Segundo aviso + aviso de reintento de cargo (PAC/PAT rechazado) | Correo | Sistema |
| +30 | Escalamiento: contacto personal | Teléfono/WhatsApp | Recaudación |
| +60 | Carta de suspensión de beneficios (cuota social) / aviso de término de cobertura (seguros, según póliza) | Correo formal | GG + Recaudación |
| +90 | Suspensión efectiva y paso a gestión especial | — | GG |

**Reglas por producto:**
- **Cuota social (fondo propio):** la suspensión de beneficios a +60/+90 es decisión interna de MundoSocios. ☐ Validar plazos.
- **Seguros (fondo de terceros):** el atraso NO puede manejarse igual — hay cobertura de un tercero de por medio. La regla de término/suspensión de cobertura la fija la póliza con la aseguradora. ☐ Levantar con la aseguradora qué dice cada póliza (insumo también para el procedimiento de pago a aseguradoras, hoy inexistente).
- **PAC/PAT rechazado:** un reintento automático a los 5 días del rechazo; si vuelve a rechazar, pasa al flujo de correo con enlace de pago alternativo. ☐ Validar.

## 2. Pagos parciales (propuesta)

| Caso | Regla propuesta | Decisión |
|---|---|---|
| Cuota social | **Sí se aceptan**, con imputación al documento más antiguo primero (FIFO). El socio queda "al día" solo con saldo cero del año. | ☐ |
| Primas de seguros | **No se aceptan parciales**: la prima cubre un período de cobertura completo. Pago incompleto = prima impaga (evita quiebres con la aseguradora en fondos de terceros). | ☐ |
| Convenios de pago (deuda acumulada) | Posibles solo con aprobación de GG, documentados (monto, cuotas, fechas) y registrados como plan de pago en el sistema — no como "ajustes" sueltos. | ☐ |

Registro contable: el pago parcial se aplica contra el documento (no cuentas puente); el saldo queda visible como CxC vencida. Prohibido rebajar deuda por glosa/ajuste manual sin documento de respaldo.

## 3. Indicadores de la política

- Morosidad por tramo (7/15/30/60/90+) por producto y cámara, mensual.
- Tasa de recuperación por etapa del escalamiento (mide si los correos funcionan — hoy PC-05, sin métricas).
- Rechazos PAC/PAT y % recuperado en el reintento.
- Nº de convenios de pago vigentes y su cumplimiento.

## 4. Qué falta para aprobar esto

1. ☐ Revisión de Oriana: plazos y canales realistas con la operación actual.
2. ☐ Definición de la aseguradora: reglas de mora/término por póliza (bloquea la fila "seguros").
3. ☐ Firma de Constanza Daniels: suspensión de beneficios y convenios de pago.
4. ☐ Traspaso a configuración: plantillas de correo (hoy Zoho, luego Odoo Follow-up) con los textos aprobados.
