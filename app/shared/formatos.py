from __future__ import annotations

import re
from datetime import date, datetime


_FECHA_ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_FECHA_ARGENTINA_RE = re.compile(r"^\d{2}/\d{2}/\d{4}$")
_PERIODO_YYYYMM_RE = re.compile(r"^\d{6}$")
_PERIODO_ARGENTINO_RE = re.compile(r"^\d{2}/\d{4}$")
_PERIODO_ARGENTINO_FECHA_RE = re.compile(r"^\d{2}/\d{2}/\d{4}$")


def formatear_fecha_iso_a_argentina(fecha_iso: str) -> str:
    if not isinstance(fecha_iso, str) or not _FECHA_ISO_RE.fullmatch(fecha_iso):
        raise ValueError("La fecha ISO debe tener formato YYYY-MM-DD.")

    try:
        fecha = date.fromisoformat(fecha_iso)
    except ValueError as exc:
        raise ValueError("La fecha ISO no es valida.") from exc

    return fecha.strftime("%d/%m/%Y")


def normalizar_fecha_argentina_a_iso(fecha_argentina: str) -> str:
    if (
        not isinstance(fecha_argentina, str)
        or not _FECHA_ARGENTINA_RE.fullmatch(fecha_argentina)
    ):
        raise ValueError("La fecha argentina debe tener formato DD/MM/YYYY.")

    try:
        fecha = datetime.strptime(fecha_argentina, "%d/%m/%Y").date()
    except ValueError as exc:
        raise ValueError("La fecha argentina no es valida.") from exc

    return fecha.isoformat()


def formatear_periodo_yyyymm_a_argentina(
    periodo_yyyymm: int | str,
    *,
    como_fecha: bool = False,
) -> str:
    anio, mes = _descomponer_periodo_yyyymm(periodo_yyyymm)

    if como_fecha:
        return f"01/{mes:02d}/{anio:04d}"

    return f"{mes:02d}/{anio:04d}"


def normalizar_periodo_argentino_a_yyyymm(periodo_argentino: str) -> int:
    if not isinstance(periodo_argentino, str):
        raise ValueError("El periodo argentino debe ser texto.")

    periodo = periodo_argentino.strip()

    if _PERIODO_ARGENTINO_RE.fullmatch(periodo):
        mes = int(periodo[:2])
        anio = int(periodo[3:])
        _validar_anio_mes(anio, mes)
        return anio * 100 + mes

    if _PERIODO_ARGENTINO_FECHA_RE.fullmatch(periodo):
        dia = int(periodo[:2])
        mes = int(periodo[3:5])
        anio = int(periodo[6:])

        if dia != 1:
            raise ValueError("El periodo como fecha debe usar dia 01.")

        _validar_anio_mes(anio, mes)
        return anio * 100 + mes

    raise ValueError("El periodo argentino debe ser MM/YYYY o 01/MM/YYYY.")


def formatear_entero_escala_a_decimal_argentino(
    valor_entero: int,
    escala: int,
) -> str:
    _validar_entero(valor_entero, "valor_entero")
    _validar_escala(escala)

    signo = "-" if valor_entero < 0 else ""
    valor_absoluto = abs(valor_entero)
    factor = 10**escala
    parte_entera, parte_decimal = divmod(valor_absoluto, factor)

    entero_formateado = _insertar_puntos_miles(str(parte_entera))

    if escala == 0:
        return f"{signo}{entero_formateado}"

    decimal_formateado = f"{parte_decimal:0{escala}d}"
    return f"{signo}{entero_formateado},{decimal_formateado}"


def normalizar_decimal_argentino_a_entero_escala(
    valor_argentino: str,
    escala: int,
) -> int:
    if not isinstance(valor_argentino, str):
        raise ValueError("El valor argentino debe ser texto.")

    _validar_escala(escala)

    valor = valor_argentino.strip()
    patron = _crear_patron_decimal_argentino(escala)

    if not patron.fullmatch(valor):
        raise ValueError("El valor argentino no respeta la escala indicada.")

    signo = -1 if valor.startswith("-") else 1
    valor_sin_signo = valor.lstrip("+-")

    if escala == 0:
        parte_entera = valor_sin_signo
        parte_decimal = ""
    else:
        parte_entera, parte_decimal = valor_sin_signo.split(",", 1)

    digitos = parte_entera.replace(".", "") + parte_decimal
    return signo * int(digitos)


def _descomponer_periodo_yyyymm(periodo_yyyymm: int | str) -> tuple[int, int]:
    if isinstance(periodo_yyyymm, bool):
        raise ValueError("El periodo YYYYMM no puede ser booleano.")

    periodo = str(periodo_yyyymm).strip()

    if not _PERIODO_YYYYMM_RE.fullmatch(periodo):
        raise ValueError("El periodo debe tener formato YYYYMM.")

    anio = int(periodo[:4])
    mes = int(periodo[4:])
    _validar_anio_mes(anio, mes)

    return anio, mes


def _validar_anio_mes(anio: int, mes: int) -> None:
    if anio < 1:
        raise ValueError("El anio del periodo debe ser mayor a cero.")

    if mes < 1 or mes > 12:
        raise ValueError("El mes del periodo debe estar entre 1 y 12.")


def _validar_entero(valor: int, nombre: str) -> None:
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise ValueError(f"{nombre} debe ser un entero.")


def _validar_escala(escala: int) -> None:
    if isinstance(escala, bool) or not isinstance(escala, int) or escala < 0:
        raise ValueError("La escala debe ser un entero mayor o igual a cero.")


def _insertar_puntos_miles(digitos: str) -> str:
    partes = []

    while digitos:
        partes.append(digitos[-3:])
        digitos = digitos[:-3]

    return ".".join(reversed(partes)) or "0"


def _crear_patron_decimal_argentino(escala: int) -> re.Pattern[str]:
    parte_entera = r"(?:\d+|\d{1,3}(?:\.\d{3})+)"
    parte_decimal = "" if escala == 0 else rf",\d{{{escala}}}"

    return re.compile(rf"^[+-]?{parte_entera}{parte_decimal}$")
