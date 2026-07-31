# Consolidador del maestro único (I-06)

Consolida los 6 mantenedores reales de `FLUJOS DE PROCESO/RECAUDACIÓN Y COBRANZA/` en el maestro único del proyecto:

- `MANT. PLAN SOCIOS 07-26.xlsx` · `MANT. COMPLEMENTARIO 07-26.xlsx` · `MANT. CATASTRÓFICO 07-26.xlsx` · `MANT. PLAN CARREÑO 07-26.xlsx` (encuentra el del mes por patrón de nombre)
- `Mantenedor Cuota Social empresa.xlsx` · `Mantenedor Cuota Social persona.xlsx`

```bash
python3 consolidador_maestro.py --carpeta "…/FLUJOS DE PROCESO/RECAUDACIÓN Y COBRANZA" --salida ./2026-08
```

**Salidas:** `MAESTRO_UNICO_MS.xlsx` (todos los productos por socio + hoja RESUMEN) · `maestro_seguros.csv` (insumo directo de `generador_devengos.py`) · `maestro_cuota_social.csv` (insumo de `generador_cuota_social.py`).

## Qué sabe del layout real (levantado 2026-07-31 contra los archivos de julio)

- El factor UF vigente es la columna `VALOR…` **más a la derecha** (`VALOR '25`/`VALOR UF actual`, `VALOR 2025`/`VALOR 2026`, `VALOR`/`VALOR 25-26`).
- Debajo del mantenedor vienen pegadas las nóminas PAC/PAT y los eliminados: se detectan por sus encabezados (`NOMBRE SEGURO`, `Estado de Cargo`, `Convenio`, `FECHA DE ELIMINACIÓN`…) y **no** se consolidan.
- Socios nuevos al final sin `Mod. Pago`: entran con medio de pago vacío y nota "socio nuevo?".
- Cuota social empresa: el N° de miembros solo está anotado si es >3; si falta, se **deriva del monto** (base 3 UF + n×1 UF) y queda anotado en OBSERVACION.
- Cuota social persona: montos distintos al estándar (ej. $39.587) pasan como `monto_clp` manual al generador.
- Filas de totales/leyendas (sin RUT válido) se descartan; RUTs con módulo 11 malo quedan en el Excel con observación pero **no** pasan a los CSV.
- Ningún mantenedor trae correo (verificado): el correo para cobranza debe venir de otra fuente.

## Reglas de operación

1. Correr **una vez al mes**, después de que Oriana actualiza los mantenedores y antes de generar devengos.
2. Revisar el `RESUMEN POR PRODUCTO`: los conteos deben calzar con los mantenedores (referencia julio-26: Plan Socios ~201 · Complementario ~511 · Catastrófico ~579 · Plan Carreño ~32 · CS empresa ~650 · CS persona ~430).
3. Si un producto sale en 0 o con conteo muy distinto, el mantenedor cambió de formato: no usar la salida, reportar.

## Tests

```bash
python3 -m unittest discover tests   # 5 tests con fixtures del layout real
```

Probada además la cadena completa: consolidador → `maestro_seguros.csv` → `generador_devengos.py` → `DEVENGO … .xlsx`, y → `maestro_cuota_social.csv` → `generador_cuota_social.py`.
