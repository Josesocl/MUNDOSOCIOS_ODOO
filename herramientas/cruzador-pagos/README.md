# Cruzador de pagos — borrador de PRECONCILIACIÓN

Ataca el dolor PC-01 (~10 h/semana cruzando Manager+, Zoho y Excel): lee la **cartola del Banco de Chile** y el **Resumen histórico de abonos de Transbank**, clasifica cada movimiento y genera un Excel con la misma estructura del archivo PRECONCILIACIÓN que hoy se arma a mano, pre-llenado.

```bash
pip install openpyxl

python3 cruzador_pagos.py \
  --cartola "CARTOLA BANCO CHILE JUNIO 26.xls" \
  --transbank-resumen "INFORME TRANSBANK Resumen_historico_abonos (06-30).xls" \
  --maestro maestro_socios.csv \
  --salida ./salida
```

Los `.xls` del banco y de Transbank son HTML disfrazado: se leen directo (también acepta `.xlsx` y CSV). Maestro: CSV con `rut;nombre` (sirve el consolidado de los mantenedores).

## Qué hace con cada tipo de movimiento

| Movimiento (glosa cartola) | Acción | Estado |
|---|---|---|
| `Pago: Abonos Debito Y Credito Transbank…` | Cuadra contra el resumen Transbank (fecha+monto, tolerancia ±2 pesos, ventana ±1 día por el desfase crédito/débito) y anota el nº de ventas del día | `listo` si cuadra |
| `Traspaso De: {nombre}` | Match difuso del nombre contra el maestro → **propone** RUT con confianza alta/media | `P` (propuesta) |
| `Pac Multibanco {banco}` | Marca "RECAUDACIÓN PAC POR DISTRIBUIR" (el detalle por socio está en la rendición PAC del banco, no en la cartola) | `P` |
| `Dep.cheq…` / depósitos | "DEPÓSITO POR IDENTIFICAR" con docto y sucursal | `P` |
| Cargos (proveedores, sueldos, previsionales, comisiones, PAC de servicios, tarjeta) | Clasificados automáticamente | `listo` |

Columnas de salida = las de la preconciliación manual (`Canal, Nro. Docto., Fecha, Descripción, Cargos, Abonos, Saldo, RUT, CONCEPTO, MODULO, CUENTA, OT, CC, LN, ESTADO`) + 3 columnas del cruzador (`CLASIFICACION, CONFIANZA, NOTA`). Lo que el cruzador no puede saber (cuenta contable, OT, CC, LN, splits multi-RUT) queda para el criterio de Recaudación — pero ya con el 70-80% del trabajo mecánico hecho.

## Límites conocidos (por diseño de las fuentes)

- **La cartola nunca trae RUT**: las propuestas por nombre son *propuestas*; confirmarlas contra la deuda antes de rebajar. Quien transfiere puede no ser el socio.
- **PAC agregado**: para distribuir la recaudación PAC por socio se necesita la **rendición PAC del banco** (fuente pendiente de integrar — pedir a Marcos/banco el archivo por convenio 16/41).
- **Ventas Transbank → socio**: los informes de Transbank no traen RUT del tarjetahabiente. El cruce determinístico requiere guardar el token de orden Webpay al generar el cobro (hoy la identificación se hace a mano en `06 TRANSBANK`).
- Los abonos del 1-2 del mes pueden no cuadrar 1:1 por arrastre de ventas de fin de mes → quedan marcados "SIN CUADRE" para revisión, no se inventa el match.

## Tests

```bash
python3 -m unittest discover tests    # 7 tests con fixtures que replican los formatos reales
```

**Primer uso:** correr con la cartola y el resumen de junio ya conciliados a mano y comparar el borrador contra la `06 PRECONCILIACIÓN JUNIO 26.xlsx` real — calibrar umbrales de confianza antes de usarlo para julio.
