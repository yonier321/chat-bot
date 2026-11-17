"""Ayudas para los mapas: enlaces de Google Maps y distancia entre dos puntos.

No necesitan clave de API: Google Maps abre estos enlaces directamente.
"""

import math
from urllib.parse import urlencode

GOOGLE_MAPS = "https://www.google.com/maps"


def _punto(parada) -> str:
    return f"{parada['latitud']},{parada['longitud']}"


def tiene_coordenadas(parada) -> bool:
    return parada is not None and parada["latitud"] is not None and parada["longitud"] is not None


def enlace_parada(parada) -> str:
    """Abre Google Maps con un pin en la parada."""
    return f"{GOOGLE_MAPS}/search/?{urlencode({'api': 1, 'query': _punto(parada)})}"


def enlace_recorrido(paradas) -> str | None:
    """Dibuja el recorrido de una ruta: primera parada -> paradas intermedias -> última."""
    con_mapa = [p for p in paradas if tiene_coordenadas(p)]
    if len(con_mapa) < 2:
        return None
    parametros = {
        "api": 1,
        "origin": _punto(con_mapa[0]),
        "destination": _punto(con_mapa[-1]),
        "travelmode": "driving",
    }
    intermedias = con_mapa[1:-1][:8]  # Google Maps acepta pocas paradas intermedias en el enlace
    if intermedias:
        parametros["waypoints"] = "|".join(_punto(p) for p in intermedias)
    return f"{GOOGLE_MAPS}/dir/?{urlencode(parametros)}"


def enlace_como_llegar(origen, destino) -> str | None:
    """Indicaciones en transporte público de una parada a otra."""
    if not (tiene_coordenadas(origen) and tiene_coordenadas(destino)):
        return None
    parametros = {"api": 1, "origin": _punto(origen), "destination": _punto(destino), "travelmode": "transit"}
    return f"{GOOGLE_MAPS}/dir/?{urlencode(parametros)}"


def distancia_metros(lat1, lon1, lat2, lon2) -> float:
    """Distancia en línea recta entre dos coordenadas (fórmula de Haversine)."""
    radio_tierra = 6_371_000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * radio_tierra * math.asin(math.sqrt(a))


def formatear_distancia(metros: float) -> str:
    return f"{metros:.0f} m" if metros < 1000 else f"{metros / 1000:.1f} km"
