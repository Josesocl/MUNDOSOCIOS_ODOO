"""Utilidades de RUT chileno (módulo 11) para el generador de devengos.

Regla del cliente (Manual Carga de Devengos): los RUT con dígito
verificador K deben ir con la K en MAYÚSCULA en el archivo de importación.
"""

import re

_RUT_RE = re.compile(r"^(\d{1,9})-([\dkK])$")


def normalizar(rut: str) -> str:
    """Normaliza un RUT a formato NNNNNNNN-D sin puntos y con K mayúscula.

    Acepta entradas con puntos, espacios y k minúscula.
    Lanza ValueError si el formato no es reconocible.
    """
    limpio = rut.strip().replace(".", "").replace(" ", "")
    if "-" not in limpio and len(limpio) > 1:
        limpio = limpio[:-1] + "-" + limpio[-1]
    m = _RUT_RE.match(limpio)
    if not m:
        raise ValueError(f"RUT con formato no reconocible: {rut!r}")
    cuerpo, dv = m.groups()
    return f"{int(cuerpo)}-{dv.upper()}"


def digito_verificador(cuerpo: int) -> str:
    """Calcula el dígito verificador por módulo 11."""
    suma, factor = 0, 2
    for c in reversed(str(cuerpo)):
        suma += int(c) * factor
        factor = 2 if factor == 7 else factor + 1
    resto = 11 - (suma % 11)
    if resto == 11:
        return "0"
    if resto == 10:
        return "K"
    return str(resto)


def es_valido(rut: str) -> bool:
    """True si el RUT normaliza y su dígito verificador es correcto."""
    try:
        norm = normalizar(rut)
    except ValueError:
        return False
    cuerpo, dv = norm.split("-")
    return digito_verificador(int(cuerpo)) == dv
