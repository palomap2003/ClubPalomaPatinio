import re
import unicodedata
from datetime import date, datetime
from zoneinfo import ZoneInfo

from .errors import ApiError

ZONA = ZoneInfo("America/Argentina/Buenos_Aires")


def ahora_ar():
    """Hora local de Argentina (sin tzinfo). Render corre en UTC, por eso no se usa datetime.now() a secas."""
    return datetime.now(ZONA).replace(tzinfo=None)


def slug(texto):
    """'Ramos Mejía' -> 'RamosMejia' (sin tildes, espacios ni símbolos)."""
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]", "", sin_tildes)


def hora_a_int(valor, campo, permitir_24=False):
    """Convierte 'HH:00' a entero (0-24). Rechaza minutos distintos de 00."""
    if not isinstance(valor, str) or not re.fullmatch(r"\d{1,2}:\d{2}", valor):
        raise ApiError(400, "HORA_INVALIDA", f"'{campo}' debe tener formato HH:MM (ej. 18:00).")
    h, m = (int(x) for x in valor.split(":"))
    if m != 0:
        raise ApiError(400, "HORA_NO_COMPLETA", f"'{campo}' debe ser una hora completa (minuto 00).")
    if h > 24 or (h == 24 and not permitir_24) or h < 0:
        raise ApiError(400, "HORA_INVALIDA", f"'{campo}' fuera de rango.")
    return h


def int_a_hora(h):
    return f"{h:02d}:00"


def parsear_fecha(valor, campo="fecha"):
    try:
        return date.fromisoformat(valor)
    except (TypeError, ValueError):
        raise ApiError(400, "FECHA_INVALIDA", f"'{campo}' debe tener formato YYYY-MM-DD.")
