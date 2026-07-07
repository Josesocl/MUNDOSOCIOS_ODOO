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

## Formato generado (según MANUAL CARGA DE DEVENGOS)

22 columnas A–V: tipo `T`, glosa `DEVENGO {SEGURO} {PERIODO}`, fecha contable = primer día del mes (`01-MM-AAAA`), correlativo, unidad de negocio `001`, glosa detalle `{RUT} {SEG} {PERIODO}`, cuenta por cobrar, monto debe = `factor_uf × UF` redondeado al peso, tipo de documento por seguro, y **última fila de contrapartida** con la cuenta de ingreso, centro de costos `MS` y el total en HABER.

| Seguro | CxC | Ingreso | Tipo doc |
|---|---|---|---|
| Plan Socios | 1130004 | 3310005 | PSOC |
| Complementario | 1130003 | 3310003 | SCOMP |
| Catastrófico | 1130002 | 3310001 | SCAT |
| Plan Carreño | 1130005 | 3310004 | PCARR |

Las glosas por seguro son configurables en el diccionario `SEGUROS` del script.

## Tests

```bash
python3 -m unittest discover tests    # 14 tests
```

**Antes del primer uso productivo:** generar el período en curso, comparar contra el archivo hecho a mano ese mismo mes (totales y 3-4 filas al azar) e importar en Manager+ un mes en paralelo antes de abandonar el proceso manual.
