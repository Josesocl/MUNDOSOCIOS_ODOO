#!/usr/bin/env python3
"""Cliente SimpleAPI (simpleapi.cl) — consulta RUT/situación tributaria SII.

Reemplaza a API Gateway como proveedor de la verificación SII del
proyecto MundoSocios (decisión 2026-07-31: API key de SimpleAPI vigente
hasta 31-07-2027).

SEGURIDAD: la API key NUNCA va en el código ni en el repositorio.
Se entrega por variable de entorno:
    export SIMPLEAPI_API_KEY="2629-N060-6395-1290-7179"

CUOTA: el plan contratado permite solo 10 consultas RUT al mes (el
contador se reinicia el día 1). Este cliente protege la cuota:
  - cachea cada respuesta en disco (por defecto 90 días), y
  - lleva un contador mensual local; se niega a consultar al llegar
    al límite salvo que se pase --forzar.
Uso previsto: SOLO altas/cambios de proveedores (bajo volumen). La
validación masiva de RUTs (socios) se hace local con módulo 11, sin
gastar cuota.

Uso:
    python3 cliente_simpleapi.py --rut 76123456-7
    python3 cliente_simpleapi.py --rut 76123456-7 --mock   # sin red ni cuota
    python3 cliente_simpleapi.py --estado                  # cuota usada del mes

CONFIGURACIÓN (confirmada por la documentación oficial, 2026-07-31):
  - URL base: https://api.simpleapi.cl        [CONFIRMADO]
  - Autenticación: header 'Authorization' con la API key directa,
    sin prefijo 'Bearer'.                      [CONFIRMADO]
  - RUTA_RUT: ruta del endpoint de la API RUT  [POR CONFIRMAR — ajustar
    con SIMPLEAPI_RUTA_RUT según la sección "API RUT" de la doc].
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "generador-devengos"))
import rut_utils

# --- Configuración ---
BASE_URL = os.environ.get("SIMPLEAPI_BASE_URL", "https://api.simpleapi.cl")  # confirmado
CABECERA_AUTH = os.environ.get("SIMPLEAPI_CABECERA_AUTH", "Authorization")   # confirmado (key directa)
RUTA_RUT = os.environ.get("SIMPLEAPI_RUTA_RUT", "/api/RUT/{rut}")            # POR CONFIRMAR en la doc

LIMITE_MENSUAL_RUT = 10          # plan contratado (API RUT)
DIAS_CACHE = 90
ARCHIVO_ESTADO = Path(__file__).with_name(".estado_simpleapi.json")

# Rutas candidatas para --descubrir (las 404 no consumen cuota: la ruta
# no existe, la consulta nunca llega al producto API RUT).
RUTAS_CANDIDATAS = [
    "/api/RUT/{rut}", "/api/rut/{rut}", "/api/Rut/{rut}",
    "/api/v1/rut/{rut}", "/api/RUT/consultar/{rut}",
    "/api/rut/consultar/{rut}", "/api/contribuyente/{rut}",
    "/api/contribuyentes/{rut}", "/api/RUT/contribuyente/{rut}",
    "/api/sii/rut/{rut}", "/rut/{rut}",
]


def _cargar_estado():
    if ARCHIVO_ESTADO.exists():
        try:
            return json.loads(ARCHIVO_ESTADO.read_text())
        except json.JSONDecodeError:
            pass
    return {"mes": "", "consultas": 0, "cache": {}}


def _guardar_estado(estado):
    ARCHIVO_ESTADO.write_text(json.dumps(estado, ensure_ascii=False, indent=1))


def _mes_actual(hoy=None):
    hoy = hoy or date.today()
    return f"{hoy.year}-{hoy.month:02d}"


def consultas_del_mes(estado, hoy=None):
    return estado["consultas"] if estado.get("mes") == _mes_actual(hoy) else 0


def _respuesta_mock(rut):
    return {"rut": rut, "razonSocial": "EMPRESA DE PRUEBA LTDA",
            "inicioActividades": True, "fechaInicioActividades": "2015-03-01",
            "actividades": [{"codigo": "620200", "descripcion":
                             "CONSULTORIA INFORMATICA", "afecta": True}],
            "_mock": True}


def consultar_rut(rut, api_key=None, mock=False, forzar=False, hoy=None,
                  _abrir=urllib.request.urlopen):
    """Consulta un RUT. Devuelve (datos, origen) con origen en
    {'cache','api','mock'}. Lanza RuntimeError con mensaje claro si no
    hay key, si la cuota mensual está agotada, o si la API falla."""
    rut = rut_utils.normalizar(rut)
    if not rut_utils.es_valido(rut):
        raise RuntimeError(f"RUT inválido (módulo 11): {rut}")
    if mock:
        return _respuesta_mock(rut), "mock"

    estado = _cargar_estado()
    en_cache = estado["cache"].get(rut)
    if en_cache:
        edad = (datetime.now() - datetime.fromisoformat(en_cache["fecha"])).days
        if edad <= DIAS_CACHE:
            return en_cache["datos"], "cache"

    usadas = consultas_del_mes(estado, hoy)
    if usadas >= LIMITE_MENSUAL_RUT and not forzar:
        raise RuntimeError(
            f"Cuota mensual de API RUT agotada ({usadas}/{LIMITE_MENSUAL_RUT}). "
            "Se reinicia el día 1. Use --forzar solo si está seguro.")

    api_key = api_key or os.environ.get("SIMPLEAPI_API_KEY")
    if not api_key:
        raise RuntimeError("Falta la API key: exporte SIMPLEAPI_API_KEY "
                           "(nunca la escriba en código ni documentos).")

    url = BASE_URL.rstrip("/") + RUTA_RUT.format(rut=rut)
    peticion = urllib.request.Request(url, headers={CABECERA_AUTH: api_key,
                                                   "Accept": "application/json"})
    try:
        with _abrir(peticion, timeout=30) as resp:
            datos = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"SimpleAPI respondió HTTP {e.code} para {rut}. "
                           "Verifique endpoint/cabecera contra la documentación "
                           "oficial y la vigencia de la key.") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"No se pudo conectar a SimpleAPI: {e.reason}") from e

    estado["mes"] = _mes_actual(hoy)
    estado["consultas"] = usadas + 1
    estado["cache"][rut] = {"fecha": datetime.now().isoformat(), "datos": datos}
    _guardar_estado(estado)
    return datos, "api"


def descubrir_ruta(rut, api_key=None, _abrir=urllib.request.urlopen):
    """Prueba las rutas candidatas hasta encontrar la que responde 200.
    Devuelve (ruta, datos) o (None, None). Imprime el avance."""
    rut = rut_utils.normalizar(rut)
    api_key = api_key or os.environ.get("SIMPLEAPI_API_KEY")
    if not api_key:
        raise RuntimeError("Falta la API key: exporte SIMPLEAPI_API_KEY.")
    for ruta in RUTAS_CANDIDATAS:
        url = BASE_URL.rstrip("/") + ruta.format(rut=rut)
        peticion = urllib.request.Request(url, headers={CABECERA_AUTH: api_key,
                                                        "Accept": "application/json"})
        try:
            with _abrir(peticion, timeout=20) as resp:
                cuerpo = resp.read().decode("utf-8", errors="replace")
            print(f"  ✔ {ruta} → HTTP 200")
            try:
                return ruta, json.loads(cuerpo)
            except json.JSONDecodeError:
                return ruta, {"_respuesta_no_json": cuerpo[:500]}
        except urllib.error.HTTPError as e:
            marca = "404" if e.code == 404 else f"{e.code} (¡la ruta existe! revisar auth/método)"
            print(f"  ✘ {ruta} → HTTP {marca}")
            if e.code in (401, 403, 405):
                return ruta, None
        except urllib.error.URLError as e:
            print(f"  ✘ {ruta} → sin conexión: {e.reason}")
            return None, None
    return None, None


def main(argv=None):
    ap = argparse.ArgumentParser(description="Consulta RUT vía SimpleAPI (SII)")
    ap.add_argument("--rut")
    ap.add_argument("--mock", action="store_true", help="respuesta simulada, sin red ni cuota")
    ap.add_argument("--forzar", action="store_true", help="ignora el límite mensual")
    ap.add_argument("--estado", action="store_true", help="muestra cuota usada del mes")
    ap.add_argument("--descubrir", action="store_true",
                    help="prueba rutas candidatas del endpoint hasta dar con la correcta")
    args = ap.parse_args(argv)

    if args.descubrir:
        if not args.rut:
            ap.error("--descubrir requiere --rut")
        try:
            ruta, datos = descubrir_ruta(args.rut)
        except RuntimeError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 1
        if ruta and datos is not None:
            print(f"\nRUTA ENCONTRADA: {ruta}")
            print("Déjela fija con:")
            print(f'  export SIMPLEAPI_RUTA_RUT="{ruta}"')
            print("\nRespuesta:")
            print(json.dumps(datos, ensure_ascii=False, indent=2))
            return 0
        if ruta:
            print(f"\nLa ruta {ruta} existe pero rechazó la consulta: revisar "
                  "API key vigente, método HTTP o formato del RUT en la "
                  "documentación oficial.")
            return 1
        print("\nNinguna ruta candidata respondió. Copiar el ejemplo de "
              "request de la sección 'API RUT' de documentacion.simpleapi.cl.")
        return 1

    if args.estado:
        estado = _cargar_estado()
        print(f"Consultas API RUT usadas este mes: {consultas_del_mes(estado)}"
              f"/{LIMITE_MENSUAL_RUT} · RUTs en caché: {len(estado['cache'])}")
        return 0
    if not args.rut:
        ap.error("indique --rut o --estado")
    try:
        datos, origen = consultar_rut(args.rut, mock=args.mock, forzar=args.forzar)
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    print(f"[origen: {origen}]")
    print(json.dumps(datos, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
