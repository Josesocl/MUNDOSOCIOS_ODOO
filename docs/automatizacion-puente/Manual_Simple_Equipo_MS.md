# Las herramientas de Recaudación — explicado simple

**Para el equipo MundoSocios** · Agosto 2026 · v1.0
*(Este es el manual corto. El detallado, con todos los casos y errores, es el "Manual de operación de la automatización".)*

---

## 1. Qué es esto (en 4 frases)

Son **programas pequeños que leen archivos Excel y producen archivos Excel**. Hacen en segundos los cruces que hoy toman horas: armar los devengos del mes, juntar los 6 mantenedores en una sola lista, y clasificar la cartola del banco para la preconciliación.

**No son inteligencia artificial**: no piensan, no deciden, no se conectan a internet, no tocan Manager+ ni el banco. Hacen siempre lo mismo, como una fórmula de Excel grande. **La decisión final siempre es de una persona**: los programas proponen, usted revisa y carga.

## 2. Dónde está cada cosa

| Qué | Dónde |
|---|---|
| Los programas | Carpeta `MUNDOSOCIOS_ODOO/herramientas/` (en el OneDrive) |
| Los archivos del mes (mantenedores, cartola, Transbank) | La carpeta de siempre: `…/FLUJOS DE PROCESO/RECAUDACIÓN Y COBRANZA/` |
| Lo que producen los programas | Subcarpetas `salida/` dentro de cada herramienta |
| El respaldo de todo | GitHub (lo administra JR — si algo se pierde, se recupera de ahí) |

## 3. Lo único que hay que saber de la Terminal

Los programas se ejecutan desde la aplicación **Terminal** del Mac (está en Aplicaciones → Utilidades, o búsquela con la lupa 🔍 escribiendo "Terminal").

1. Abrir Terminal. Aparece una ventana con texto y un cursor.
2. **Copiar** el comando completo desde este manual (todas sus líneas juntas).
3. **Pegarlo** en la Terminal (Cmd+V) y apretar **Enter**.
4. Esperar. El programa imprime un resumen. **Leer ese resumen** — ahí dice qué hizo y si algo requiere revisión.

Reglas simples:
- Los comandos se copian **completos, tal cual** — no cambiar ni una letra.
- Si aparece un mensaje de error, **no adivinar**: copiar TODO el texto del error y enviárselo a JR. Nada se rompe por un error; el programa simplemente no hizo nada.

## 4. El ciclo de cada mes — 3 pasos

### Paso A (día 1-9) — Juntar los mantenedores en una sola lista
*Lo corre: quien actualiza los mantenedores (Oriana).* Después de actualizar los 4 mantenedores de seguros del mes:

```bash
cd ~/"Library/CloudStorage/OneDrive-IBSolucionLtda/Documentos OneD IBS/MUNDOSOCIOS_ODOO/herramientas/consolidador-maestro"
python3 consolidador_maestro.py \
  --carpeta ~/"Library/CloudStorage/OneDrive-IBSolucionLtda/Documentos OneD IBS/CONSULTORÍA JR JOTTAR/CLIENTES CONSULTORA JRJ/MUNDOSOCIOS ODOO/FLUJOS DE PROCESO/RECAUDACIÓN Y COBRANZA" \
  --salida ./salida
```

**Qué revisar:** el resumen dice cuántos socios leyó por seguro (referencia: Plan Socios ~201 · Complementario ~467 · Catastrófico ~577 · Carreño ~32). Si un número cambia mucho sin razón, avisar a JR.

### Paso B (después del día 9) — Generar los devengos de seguros
*Lo corre: quien hace los devengos hoy.* Necesita las UF del mes (de sii.cl): la general, la del día 9 (Complementario) y la del último día del mes anterior (Catastrófico).

```bash
cd ~/"Library/CloudStorage/OneDrive-IBSolucionLtda/Documentos OneD IBS/MUNDOSOCIOS_ODOO/herramientas/generador-devengos"
python3 generador_devengos.py \
  --maestro ../consolidador-maestro/salida/maestro_seguros.csv \
  --periodo 08-2026 \
  --uf 40845.32 \
  --uf-seguro "COMPLEMENTARIO=40871.10" \
  --uf-seguro "CATASTROFICO=40763.55" \
  --salida ./salida
```
*(cambiar `08-2026` por el mes real y los tres valores de UF por los reales)*

**Qué revisar:** los totales por seguro contra el mes anterior. Si cuadran, cargar los 4 archivos `DEVENGO … .xlsx` en Manager+ **igual que siempre** (Importador de datos). Nada cambia en esa parte.

### Paso C (primeros días del mes siguiente) — Borrador de la preconciliación
*Lo corre: quien concilia (Fran/Oriana), con los archivos que entrega Marcos.* Antes: guardar la cartola y el informe Transbank como `.xlsx` (abrirlos en Excel → Guardar como → Libro de Excel).

```bash
cd ~/"Library/CloudStorage/OneDrive-IBSolucionLtda/Documentos OneD IBS/MUNDOSOCIOS_ODOO/herramientas/cruzador-pagos"
python3 cruzador_pagos.py \
  --cartola ~/"Library/CloudStorage/OneDrive-IBSolucionLtda/Documentos OneD IBS/CONSULTORÍA JR JOTTAR/CLIENTES CONSULTORA JRJ/MUNDOSOCIOS ODOO/FLUJOS DE PROCESO/RECAUDACIÓN Y COBRANZA/CARTOLA BANCO CHILE JULIO 26.xlsx" \
  --transbank-resumen ~/"Library/CloudStorage/OneDrive-IBSolucionLtda/Documentos OneD IBS/CONSULTORÍA JR JOTTAR/CLIENTES CONSULTORA JRJ/MUNDOSOCIOS ODOO/FLUJOS DE PROCESO/RECAUDACIÓN Y COBRANZA/INFORME TRANSBANK Resumen_historico_abonos (07-31).xlsx" \
  --maestro ../consolidador-maestro/salida/maestro_seguros.csv \
  --diccionario salida-junio/diccionario_nombre_rut.csv \
  --salida ./salida-julio
```
*(cambiar los nombres de archivo por los del mes)*

**Qué produce:** `PRECONCILIACION_BORRADOR.xlsx` — la misma planilla de preconciliación de siempre, pero ya clasificada. Cada fila trae una columna **CONFIANZA**:
- **alta** = ya se identificó igual en meses anteriores → verificar rápido.
- **media** = el nombre se parece a un socio → **confirmar contra la deuda antes de usar**.
- **vacía** = el programa no sabe → identificar a mano, como siempre.

**Al terminar de conciliar el mes**, un último comando le "enseña" al programa lo que usted resolvió a mano, para que el próximo mes proponga más y mejor:

```bash
python3 calibrar_preconciliacion.py \
  --real "LA PRECONCILIACIÓN TERMINADA DEL MES.xlsx" \
  --borrador salida-julio/PRECONCILIACION_BORRADOR.xlsx \
  --salida salida-julio
```

## 5. Las 3 reglas de oro

1. **Agosto y septiembre se corren EN PARALELO** con el proceso manual de siempre. Solo cuando los totales cuadren dos meses seguidos se abandona lo antiguo.
2. **Los programas nunca cargan nada**: a Manager+ y al banco solo sube lo que una persona revisó.
3. Una propuesta de RUT **es una propuesta**, no un dato. Ante la duda, se confirma contra la deuda del socio.

## 6. Si algo sale mal

Copiar todo el mensaje de la Terminal y enviárselo a **JR Jottar** (jrjottar@ibsolucion.com). No intentar arreglar los programas ni editar sus archivos. Lo peor que puede pasar con un error es que el programa no produzca nada — los archivos originales nunca se modifican.
