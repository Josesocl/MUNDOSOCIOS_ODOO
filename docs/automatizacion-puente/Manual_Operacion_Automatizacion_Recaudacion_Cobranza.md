# Manual de operación — Automatización de Recaudación y Cobranza

**Proyecto:** MundoSocios (CChC) · **Versión:** 1.0 · **Fecha:** 2026-07-31
**Para:** el equipo que opera el proceso (Marcos, Fran, Oriana; supervisa Patricio)
**Nivel:** paso a paso, sin conocimientos de programación. Si algo no coincide con lo que ve en pantalla, deténgase y consulte — no improvise.

---

## 0. Qué hace cada herramienta (mapa general)

| Herramienta | Reemplaza el trabajo manual de… | Cuándo se usa |
|---|---|---|
| `consolidador_maestro.py` | Consolidar los 6 mantenedores en una sola lista | 1 vez al mes, al inicio |
| `generador_devengos.py` | Armar a mano `DEVENGO PLAN SOCIOS JUL-26.xlsx`, `DEVENGO COMPLEMENTARIO JUL-26.xlsx`, `DEVENGO CATASTRÓFICO JUL-26.xlsx`, `DEVENGO PLAN CARREÑO JUL-26.xlsx` | 1 vez al mes (después del día 9) |
| `generador_cuota_social.py` | Armar `DEVENGO CUOTA SOCIAL EMPRESA ENE-26.xlsx` y `DEVENGO CUOTA SOCIAL PERSONA ENE-26.xlsx` | 1 vez al año (enero) |
| `cruzador_pagos.py` | El primer barrido de `06 PRECONCILIACIÓN JUNIO 26.xlsx` (clasificar la cartola y cuadrar Transbank) | 1 vez al mes, después del cierre |
| `cliente_simpleapi.py` | Consultar `zeus.sii.cl` con captcha para cada proveedor nuevo | Solo al crear/modificar un proveedor |

**Regla de oro:** las herramientas **no tocan Manager+ ni el banco**. Solo leen archivos y producen archivos. La carga a Manager+ y la revisión final siguen siendo de una persona.

---

## 1. Instalación (una sola vez, en el equipo del área MS)

1. Verificar Python: abrir **Terminal** (Mac) y escribir `python3 --version`. Debe responder `Python 3.9` o superior. En Mac ya viene instalado.
2. Instalar la única librería necesaria:
   ```bash
   pip3 install openpyxl
   ```
3. Copiar la carpeta `herramientas/` del repositorio (`github.com/Josesocl/MUNDOSOCIOS_ODOO`) a una carpeta local del equipo, por ejemplo `Documentos/AutomatizacionMS/herramientas/`. Si el equipo tiene git: `git clone` del repositorio y listo.
4. Crear una carpeta de trabajo mensual, por ejemplo `Documentos/AutomatizacionMS/2026-08/`, donde se copiarán los archivos del mes.
5. Solo para el paso 6 (SimpleAPI): pegar al final del archivo `~/.zshrc` la línea `export SIMPLEAPI_API_KEY="LA_KEY_DEL_PANEL"` y cerrar/abrir la Terminal.

> **Importante:** los comandos de este manual asumen que usted está "parado" en la carpeta de la herramienta. Antes de cada comando, ejecute el `cd` que se indica. Los nombres con espacios o tildes **siempre van entre comillas**.

---

## 2. Ciclo mensual — paso a paso

### Paso 1 (día 1-9): actualizar mantenedores y regenerar el maestro único

**Responsable:** Oriana.

1. Actualizar como siempre los 6 mantenedores del mes en OneDrive (`FLUJOS DE PROCESO/RECAUDACIÓN Y COBRANZA/`):
   - `MANT. PLAN SOCIOS 07-26.xlsx`
   - `MANT. COMPLEMENTARIO 07-26.xlsx`
   - `MANT. CATASTRÓFICO 07-26.xlsx`
   - `MANT. PLAN CARREÑO 07-26.xlsx`
   - `Mantenedor Cuota Social empresa.xlsx`
   - `Mantenedor Cuota Social persona.xlsx`
   *(el nombre cambia de mes: 07-26, 08-26, …)*
2. Generar el maestro único:
   ```bash
   cd "Documentos/AutomatizacionMS/herramientas/consolidador-maestro"
   python3 consolidador_maestro.py --carpeta "RUTA A LA CARPETA RECAUDACIÓN Y COBRANZA" --salida "../../2026-08"
   ```
3. **Qué debe ver:** un resumen por mantenedor (filas leídas, filas incorporadas, avisos) y dos archivos nuevos en la carpeta del mes:
   - `MAESTRO_UNICO_MS.xlsx` — todos los productos por socio (para revisión humana).
   - `maestro_seguros.csv` y `maestro_cuota_social.csv` — los insumos que usan los generadores.
4. **Control:** el resumen imprime el total de registros por producto. Compárelo contra el conteo de cada mantenedor. Si un producto trae 0 filas, el mantenedor cambió de formato: no siga, reporte.

### Paso 2 (después del día 9): generar los 4 devengos de seguros

**Responsable:** quien hace hoy los devengos (con supervisión de Patricio el primer mes).

1. Buscar los valores de la UF en `sii.cl` (o `valoruf.cl`):
   - UF del **día 9 del mes** → para el Complementario.
   - UF del **último día del mes anterior** → para el Catastrófico.
   - UF del día que usan hoy para Plan Socios y Plan Carreño → es el valor `--uf` general.
2. Ejecutar (ejemplo agosto 2026, valores de UF ilustrativos — **use los reales**):
   ```bash
   cd "Documentos/AutomatizacionMS/herramientas/generador-devengos"
   python3 generador_devengos.py \
     --maestro "../../2026-08/maestro_seguros.csv" \
     --periodo 08-2026 \
     --uf 40845.32 \
     --uf-seguro "COMPLEMENTARIO=40871.10" \
     --uf-seguro "CATASTROFICO=40763.55" \
     --salida "../../2026-08"
   ```
3. **Qué debe ver:** un resumen por seguro (N° de pólizas y total en pesos) y 4 archivos en la carpeta del mes, con los mismos nombres de siempre:
   `DEVENGO PLAN SOCIOS AGO-26.xlsx` · `DEVENGO COMPLEMENTARIO AGO-26.xlsx` · `DEVENGO CATASTRÓFICO AGO-26.xlsx` · `DEVENGO PLAN CARREÑO AGO-26.xlsx`
4. **Control antes de cargar:** comparar el total de cada archivo contra el mes anterior (deben moverse solo por altas/bajas y variación de UF). Abrir uno y revisar 2-3 socios al azar: prima = factor × UF del seguro.
5. Cargar en Manager+ como siempre: **Mantenedores → Importador de datos → Comprobantes contables con documento** (el procedimiento detallado de la carga es el `MANUAL CARGA DE DEVENGOS` de siempre; no cambia nada de esa parte).
6. Si un RUT del maestro no existe en Manager+, el generador lo detiene con la lista de RUTs faltantes: crear esos clientes primero (ver `MANUAL CREACIÓN DE CLIENTES`) y volver a ejecutar. Para activar esta validación, exportar los clientes desde Manager+ (**Mantenedores → Exportador de datos → Clientes**) y agregar `--clientes clientes_manager.csv` al comando.

### Paso 3 (día 1-5 del mes siguiente): preconciliación

**Responsable:** Fran u Oriana. **Insumos que entrega Marcos** (los mismos de hoy):

| Archivo del mes (nombres reales de junio) | De dónde sale |
|---|---|
| `CARTOLA BANCO CHILE JUNIO 26.xls` | Banco de Chile, cuenta 8001104309 — descarga **en Excel** (no PDF, no TXT: el TXT es solo la nómina de pagos) |
| `INFORME TRANSBANK Resumen_historico_abonos (06-30).xls` | Portal Transbank → Resumen histórico de abonos |
| `maestro_seguros.csv` | Generado en el Paso 1 |

1. Copiar los 3 archivos a la carpeta del mes.
2. Ejecutar:
   ```bash
   cd "Documentos/AutomatizacionMS/herramientas/cruzador-pagos"
   python3 cruzador_pagos.py \
     --cartola "../../2026-08/CARTOLA BANCO CHILE JULIO 26.xls" \
     --transbank-resumen "../../2026-08/INFORME TRANSBANK Resumen_historico_abonos (07-31).xls" \
     --maestro "../../2026-08/maestro_seguros.csv" \
     --salida "../../2026-08"
   ```
3. **Qué debe ver:** `PRECONCILIACION_BORRADOR.xlsx` en la carpeta del mes, con el mismo formato de `06 PRECONCILIACIÓN JUNIO 26.xlsx` más 3 columnas de apoyo: **CLASIFICACION** (Transbank/PAC/transferencia/cargo), **CONFIANZA** (alta/media/baja) y **NOTA**.
4. **Trabajo humano que queda:** revisar solo las filas con CONFIANZA media/baja; identificar las transferencias sin RUT; distribuir los abonos "Pac Multibanco" por socio (el banco los entrega agregados — límite del banco, se resuelve cuando llegue la rendición por convenio, insumo I-01). Al terminar, guardar como `08 PRECONCILIACIÓN AGOSTO 26.xlsx` en OneDrive, como siempre.
5. **Nota técnica:** los `.xls` del banco y de Transbank son en realidad páginas web disfrazadas — la herramienta los lee igual. Si alguna vez uno no se deja leer, abrirlo en Excel, **Guardar como → .xlsx**, y reintentar con ese.

### Paso 4 (por evento): alta o modificación de proveedor

**Responsable:** quien hace el alta (hoy Cecilia / tesorería).

```bash
cd "Documentos/AutomatizacionMS/herramientas/sii-simpleapi"
python3 cliente_simpleapi.py --rut 76123456-7
```

- Devuelve del SII: razón social, giro (con código), si presenta inicio de actividades, domicilio y correo de intercambio → con eso se llena el checklist del proveedor (razón social/giro/dirección deben **coincidir**; sin inicio de actividades = **NO APTO**).
- El plan permite **10 consultas al mes**: la herramienta las cuenta, guarda cada respuesta 90 días (repetir un RUT no gasta cuota) y se bloquea al llegar al límite. `--estado` muestra cuántas van. **Nunca** consultar RUTs masivamente por esta vía — la validación masiva de RUTs es local (módulo 11) y gratis, ya incluida en generadores y cruzador.

---

## 3. Ciclo anual (solo enero): devengo de cuota social

1. Oriana actualiza `Mantenedor Cuota Social empresa.xlsx` (con N° de miembros por empresa) y `Mantenedor Cuota Social persona.xlsx`; se regenera el maestro (Paso 1).
2. Con la UF de cierre que defina Patricio (pendiente D-02: enero/febrero/marzo):
   ```bash
   cd "Documentos/AutomatizacionMS/herramientas/generador-devengos"
   python3 generador_cuota_social.py --maestro "../../2027-01/maestro_cuota_social.csv" \
     --anio 2027 --uf 39731.77 --salida "../../2027-01"
   ```
3. Produce `DEVENGO CUOTA SOCIAL EMPRESA ENE-27.xlsx` y `DEVENGO CUOTA SOCIAL PERSONA ENE-27.xlsx` con las reglas vigentes (persona 1 UF; empresa 3 UF hasta 3 miembros + 1 UF por miembro desde el 4°; cuentas CSPER/CSEMP verificadas). Control y carga igual que el Paso 2.

---

## 4. Errores frecuentes y qué hacer

| Mensaje / síntoma | Causa | Qué hacer |
|---|---|---|
| `can't open file '...'` | La Terminal no está "parada" donde está el archivo | Ejecutar primero el `cd` del paso; verificar con `ls` que el archivo se ve |
| `No such file or directory` con un nombre con espacios | Faltan las comillas | Poner la ruta completa entre comillas `"..."` |
| `RUT inválido (módulo 11): ...` | RUT mal digitado en el mantenedor | Corregir en el mantenedor y regenerar el maestro |
| Lista de "RUTs no existen en Manager+" | Socios nuevos sin cliente creado | Crearlos en Manager+ (`MANUAL CREACIÓN DE CLIENTES`) y reintentar |
| `Cuota mensual de API RUT agotada (10/10)` | Se usaron las 10 consultas SII del mes | Esperar al día 1; el caché sigue respondiendo RUTs ya consultados. `--forzar` solo con autorización de Patricio |
| La cartola no se deja leer | Formato raro del banco | Abrir en Excel → Guardar como `.xlsx` → reintentar |
| Un producto del maestro sale con 0 filas | El mantenedor cambió de formato (columnas renombradas/movidas) | No continuar; reportar al consultor con el archivo del mes |
| Totales no cuadran contra el mes anterior | Altas/bajas reales o UF mal digitada | Verificar primero la UF usada (es la causa más común) |

## 5. Calendario resumen

| Cuándo | Qué | Comando/acción | Quién |
|---|---|---|---|
| Día 1-9 | Mantenedores del mes + maestro único | `consolidador_maestro.py` | Oriana |
| Día 9-12 | 4 devengos de seguros + carga | `generador_devengos.py` → Importador Manager+ | Devengos de hoy |
| Día 1-5 (mes sgte.) | Borrador de preconciliación | `cruzador_pagos.py` → revisión humana → `NN PRECONCILIACIÓN MES 26.xlsx` | Fran/Oriana (insumos: Marcos) |
| Por evento | Verificación SII proveedor | `cliente_simpleapi.py --rut ...` | Cecilia/tesorería |
| Enero | Devengo anual cuota social | `generador_cuota_social.py` | Devengos + Patricio (UF) |
| Diario (sin cambio) | Cierre diario a Addval (48 h para subir a Manager+) | correo de siempre | Marcos |

## 6. Qué NO hacen las herramientas (para que nadie se confunda)

- No cargan nada a Manager+ ni al banco: **siempre** hay una persona que revisa y carga.
- No distribuyen el PAC por socio (falta la rendición por convenio del banco — insumo I-01).
- No identifican al tarjetahabiente de una venta Webpay (Transbank no entrega el RUT).
- No envían correos de cobranza (eso es la Ola 2, con Zoho Campaigns y textos aprobados).
- No deciden morosidad ni eliminaciones: eso lo define la política (borrador en `docs/fase-0/`).

**Primer mes (agosto): todo se corre EN PARALELO al proceso manual de siempre y se cuadran totales. Recién cuando cuadren dos meses seguidos se abandona el proceso viejo.**
