"""Validación de lo que escribe el usuario. Cada función devuelve un mensaje de error o None."""

import re

LETRAS = re.compile(r"[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ]")


def validar_nombre_parada(texto: str) -> str | None:
    texto = texto.strip()
    if len(texto) < 3:
        return "Escribe al menos 3 letras del nombre de la parada."
    if len(texto) > 50:
        return "El nombre es muy largo. Escribe máximo 50 caracteres."
    if not LETRAS.search(texto):
        return "El nombre debe tener letras, por ejemplo: <i>Parque Berrío</i>."
    return None


def validar_descripcion(texto: str) -> str | None:
    texto = texto.strip()
    if len(texto) < 5:
        return "La descripción es muy corta. Cuéntanos un poco más (mínimo 5 caracteres)."
    if len(texto) > 300:
        return f"La descripción es muy larga ({len(texto)} caracteres). El máximo es 300."
    return None
