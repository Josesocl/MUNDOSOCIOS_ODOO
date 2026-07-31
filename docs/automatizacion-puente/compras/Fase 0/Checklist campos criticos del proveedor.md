# Checklist de campos críticos del proveedor — MundoSocios

**Versión:** 2.0 · **Fecha:** 2026-07-02 (actualiza v1.0 del 2026-06-18) · **Responsable:** Patricio Fernández
**Propósito:** garantizar que un proveedor tenga todos los datos necesarios **antes** de avanzar a OC y, sobre todo, que **no falle la nómina/TXT bancario**.

> Esta versión amplía la v1.0 con representantes legales, dirección completa, tipo de documento tributario (DTE) y **verificación cruzada contra el SII**, implementada en `Automatizacion Puente Compras/Herramientas Operativas/01_Ficha_Proveedor_MundoSocios.xlsx`.

## 1. Datos de identificación (Empresa)
- [ ] RUT (sin puntos, con dígito verificador)
- [ ] Razón social
- [ ] Nombre de fantasía
- [ ] Giro / actividad
- [ ] Correo, Dirección, Comuna, Ciudad, Región, País, Teléfono

## 2. Representantes legales
- [ ] Representante Legal 1: nombre completo, RUT, correo, teléfono
- [ ] Representante Legal 2 (si aplica): mismos datos

## 3. Documento tributario
- [ ] Tipo de DTE que emite (Factura Electrónica, Factura Exenta, Boleta Electrónica, Boleta de Honorarios, etc.)

## 4. Datos bancarios (críticos para el TXT)
> Si falta cualquiera de estos, el archivo de pago a Banco de Chile falla. **Son bloqueantes.**
- [ ] Banco
- [ ] Tipo de cuenta (corriente / vista / ahorro)
- [ ] Número de cuenta
- [ ] Email para aviso de pago

## 5. Condiciones comerciales
- [ ] Forma de pago (caja chica / crédito en nómina)
- [ ] Plazo de pago (días)
- [ ] Moneda

## 6. Verificación cruzada contra el SII (manual, Fase 1)
Consultar el RUT en el SII (situación tributaria de terceros) y registrar:
- [ ] Razón Social según SII → ¿coincide con lo ingresado?
- [ ] Giro según SII → ¿coincide?
- [ ] Dirección según SII → ¿coincide?
- [ ] Documentos DTE autorizados según SII → ¿el tipo de DTE declarado está autorizado?
- [ ] Situación tributaria SII (Vigente / No vigente / Pendiente)

## 7. Regla de avance
Un proveedor pasa de **"En validación"** a **"Apto"** solo cuando:
1. Situación SII = **Vigente**, y
2. **Todos** los campos de la sección 4 (bancarios) están completos, y
3. Las 4 verificaciones de la sección 6 (Razón Social, Giro, Dirección, DTE) coinciden con el SII.

Mientras no cumpla lo anterior, la OC asociada **no puede emitirse**.

## 8. Validación
- [ ] Adm. y Finanzas confirma, contra un caso real reciente, que esta lista cubre todo lo que el TXT exige.
- [x] Confirmar si Nómina de Pago (herramienta 03) también debe validar/mostrar los datos bancarios del proveedor al momento de pagar — **resuelto 2026-07-06:** `03_Control_Nomina_Pago_MundoSocios.xlsx` incorporó una hoja `Proveedores` (espejo de este archivo) y columnas de cruce (Banco/N Cuenta/Estado de la ficha + alerta si no coinciden con lo tipeado en la nómina), verificado con recálculo real (0 errores).
