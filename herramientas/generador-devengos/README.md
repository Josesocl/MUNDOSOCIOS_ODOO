# Generador de devengos de seguros — Manager+

Reemplaza el proceso manual de **copiar los 4 Excel del mes anterior** (dolor PC-06 del Blueprint de Recaudación): a partir de un **maestro único de pólizas** genera los archivos de importación de 22 columnas para Manager+ (uno por seguro), con el período, la UF y las glosas correctas, y **valida antes de importar** todo lo que hoy rebota en el importador.

## Qué valida antes de generar

- RUT: formato, dígito verificador (módulo 11) y **K en mayúscula** (regla del manual).
- Duplicados (mismo RUT dos veces en el mismo seguro).
- Seguro conocido (Plan Socios / Complementario / Catastrófico / Plan Carreño) y factor UF > 0.
- Con `--clientes` (export de clientes de Manager+): informa qué socios **no existen aún como cliente**, para crearlos ANTES de importar y eliminar el ciclo "Cliente no existe → crear → reimportar".

Si hay errores, **no genera nada** y lista los problemas con número de línea.

## Uso

```bash
pip install openpyxl   # única dependencia

python3 generador_devengos.py \
  --maestro maestro_polizas.csv \
  --periodo 07-2026 \
  --uf 39486.29 \
  --clientes clientes_manager.csv \
  --salida "./DEVENGOS 07-2026"
```

Salida: `DEVENGO PLAN SOCIOS JUL-26.xlsx`, `DEVENGO COMPLEMENTARIO JUL-26.xlsx`, etc., listos para `Manager+ > Mantenedores > Importador de datos > Comprobantes contables con documentos` (marcar "archivo incluye encabezado"), más un resumen en pantalla con pólizas y total HABER por archivo **para cuadrar contra el mantenedor antes de importar**.

## El maestro de pólizas

Un solo CSV (separador `;` o `,`) que reemplaza a los 4 mantenedores de Drive:

| Columna | Contenido |
|---|---|
| `rut` | RUT del titular (con o sin puntos; la K se normaliza a mayúscula) |
| `nombre` | Nombre (solo para reportes) |
| `seguro` | `PLAN SOCIOS` · `COMPLEMENTARIO` · `CATASTROFICO` · `PLAN CARRENO` (acepta variantes con acentos) |
| `factor_uf` | Factor UF mensual de la póliza (ej: `3,55`) |
| `medio_pago` | Opcional: `PAC` / `PAT` / `DIRECTA` / `EMPRESA` (informativo) |

Ver `maestro_ejemplo.csv`. Para poblarlo la primera vez: consolidar los 4 mantenedores actuales de la carpeta Drive "Devengo Seguros Manager+" (columnas RUT, nombre, factor UF, medio de pago). Ese mismo maestro es después **el insumo de migración a Odoo Suscripciones** (~1.500 pólizas).

## Formato generado (verificado contra los archivos productivos JUL-26, 2026-07-07)

22 columnas A–V: tipo `T`, glosa comprobante `DEVENGO {SEG} {MMM AA}`, fecha contable = primer día del mes (celda de fecha real), correlativo, unidad de negocio `001`, glosa detalle `{RUT} {SEG} {MMM-AA}`, cuenta por cobrar, monto debe = `factor_uf × UF` redondeado al peso, tipo de documento, **Conceptos 1/2 = `99999`/`500`** en todas las filas, y **última fila de contrapartida** con la cuenta de ingreso, centro de costos `MS` y el total en HABER.

| Seguro | CxC | Ingreso | Tipo doc | Glosa detalle | UF que usa |
|---|---|---|---|---|---|
| Plan Socios | 1130004 | 3310005 | PSOC | `P SOC` | propia |
| Complementario | 1130003 | 3310003 | SCOMP | `S COM` | **día 9** |
| Catastrófico | 1130002 | 3310001 | SCAT | `S CAT` | **último día mes anterior** |
| Plan Carreño | 1130005 | 3310004 | PCARR | `P CARR` | propia |

Cada seguro puede llevar su propia UF: `--uf 40845 --uf-seguro "CATASTROFICO=40763" --uf-seguro "COMPLEMENTARIO=40892"`. Glosas y conceptos configurables en el diccionario `SEGUROS`.

## Devengo anual de cuota social

`generador_cuota_social.py` genera los archivos `DEVENGO CUOTA SOCIAL EMPRESA/PERSONA ENE-AA.xlsx` con las reglas 2026 verificadas: persona **1 UF** (1150002→3210001, CSPER), empresa **3 UF hasta 3 miembros + 1 UF por miembro desde el 4º** (1150001→3210002, CSEMP), CC contrapartida `ADM`, glosa `{RUT} CE|CP {AA} {CÁMARA}`, sin conceptos. Soporta `monto_clp` manual por fila para prorrateos.

```bash
python3 generador_cuota_social.py --maestro maestro_socios.csv --anio 2027 --uf 40500 --salida ./out
# maestro: rut;nombre;tipo_socio;camara;miembros;monto_clp
```

## Tests

```bash
python3 -m unittest discover tests    # 19 tests
```

**Validación ya hecha:** los montos generados cuadran con los archivos reales (Plan Carreño JUL-26: 0,2 UF × $40.845 = $8.169 ✓; cuota empresa ENE-26: 3 UF × $39.731,77 = $119.195 ✓, 4 UF = $158.927 ✓; persona $39.732 ✓). **Antes del primer uso productivo:** generar el período en curso desde el maestro consolidado y comparar contra el archivo hecho a mano (totales y filas al azar).
