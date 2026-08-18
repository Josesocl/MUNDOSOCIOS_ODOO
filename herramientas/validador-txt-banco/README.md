# Validador del TXT de nómina de pagos (Banco de Chile)

Cierra el tramo final del flujo de compras (Manual nóminas de pago, dolor #1
del diagnóstico — PC-P1 / DP-08): valida el `Transfer_CHILE*.txt` que genera
Manager+ **antes** de cargarlo al banco, y corrige la fecha de pago del
encabezado sin editar a mano en Bloc de notas.

## Uso

```bash
# 1. Validar (siempre, antes de cargar al banco)
python3 validador_txt_banco.py "Transfer_CHILE$_20260818_1349.txt"

# 2. Corregir la fecha de abono (reemplaza la edición manual del encabezado)
python3 validador_txt_banco.py "Transfer_CHILE$_20260818_1349.txt" --fecha-pago 22-08-2026
#    → escribe Transfer_..._pago_20260822.txt (el original no se toca);
#      ese archivo nuevo es el que se carga al banco.

# 3. Ver la estructura con dígitos enmascarados (para calibrar sin exponer montos/RUTs)
python3 validador_txt_banco.py archivo.txt --diagnostico
```

## Qué revisa

| Chequeo | Resultado |
|---|---|
| Caracteres que el banco rechaza (símbolos fuera de la lista permitida) | ERROR — no cargar |
| Líneas de más de 400 caracteres (descripciones largas) | ERROR — no cargar |
| Tildes y símbolos dudosos en glosas | aviso — revisar |
| Posibles montos negativos (anticipos / notas de crédito) | aviso — ajustar en tesorería antes de emitir |
| Estructura de registros inconsistente (línea cortada) | aviso |
| Codificación y fin de línea del archivo | informativo (se preservan al corregir) |

Códigos de salida: `0` OK · `2` errores (no cargar) · `1` error de uso.

## Calibración pendiente (con un TXT real)

El validador funciona desde ya con chequeos independientes del layout. Para
sumar los chequeos que dependen de las posiciones exactas (cuadrar el total
del encabezado contra la suma de los documentos, validar módulo 11 de cada
RUT beneficiario, cruzar contra el maestro de proveedores — RF-06b), hay que
correr `--diagnostico` sobre un TXT real de Manager+ y calibrar con esa
salida (los dígitos van enmascarados: no expone montos ni RUTs).

## Tests

```bash
python3 -m unittest discover tests    # 9 tests, sin red
```
