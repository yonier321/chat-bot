"""Consultar rutas y paradas (solo lectura, sin conversación)."""

from html import escape

from telegram import Update
from telegram.ext import ContextTypes

import database
import mapas
import teclados
from database import TIPOS_REPORTE
from handlers.menu import responder


def obtener_id(update: Update) -> int | None:
    """Saca el número del callback_data, por ejemplo 'ruta:3' -> 3."""
    try:
        return int(update.callback_query.data.split(":")[1])
    except (IndexError, ValueError):
        return None


# ─── Rutas ────────────────────────────────────────────


async def listar_rutas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rutas = database.listar_rutas()
    if not rutas:
        await responder(update, "No hay rutas registradas todavía.", teclados.volver_menu())
        return
    await responder(
        update,
        f"🚌 <b>Rutas disponibles</b> ({len(rutas)})\nToca una ruta para ver el detalle:",
        teclados.lista(rutas, "ruta", lambda r: f"{r['codigo']} · {r['nombre']}"),
    )


async def detalle_ruta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ruta_id = obtener_id(update)
    ruta = database.obtener_ruta(ruta_id) if ruta_id else None
    if not ruta:
        await responder(update, "⚠️ Esa ruta ya no existe.", teclados.volver_menu())
        return

    paradas = database.paradas_de_ruta(ruta_id)
    lineas_paradas = "\n".join(f"  {i}. {p['nombre']}" for i, p in enumerate(paradas, start=1))

    texto = (
        f"🚌 <b>{ruta['codigo']} · {escape(ruta['nombre'])}</b>\n\n"
        f"🛣️ <b>Recorrido:</b> {escape(ruta['recorrido'])}\n"
        f"🕐 <b>Horario:</b> {ruta['horario']}\n"
        f"⏱️ <b>Frecuencia:</b> cada {ruta['frecuencia']} minutos\n\n"
        f"🚏 <b>Paradas</b> (en orden):\n{lineas_paradas}"
    )

    reportes = database.reportes_recientes(ruta_id)
    if reportes:
        texto += "\n\n⚠️ <b>Reportes de las últimas 24 horas:</b>"
        for r in reportes:
            hora = r["fecha"][11:16]
            detalle = f" — {escape(r['descripcion'])}" if r["descripcion"] else ""
            texto += f"\n  • {hora} {TIPOS_REPORTE.get(r['tipo'], r['tipo'])}{detalle}"
    else:
        texto += "\n\n✅ Sin problemas reportados en las últimas 24 horas."

    await responder(update, texto, teclados.detalle_ruta(ruta_id, mapas.enlace_recorrido(paradas)))


# ─── Paradas ──────────────────────────────────────────


async def listar_paradas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    paradas = database.listar_paradas()
    if not paradas:
        await responder(update, "No hay paradas registradas todavía.", teclados.volver_menu())
        return
    await responder(
        update,
        f"🚏 <b>Paradas</b> ({len(paradas)})\nToca una para ver qué rutas pasan por ahí:",
        teclados.lista(paradas, "parada", lambda p: p["nombre"], columnas=2),
    )


async def detalle_parada(update: Update, context: ContextTypes.DEFAULT_TYPE):
    parada_id = obtener_id(update)
    parada = database.obtener_parada(parada_id) if parada_id else None
    if not parada:
        await responder(update, "⚠️ Esa parada ya no existe.", teclados.volver_menu())
        return

    rutas = database.rutas_de_parada(parada_id)
    texto = f"🚏 <b>{escape(parada['nombre'])}</b>\n\n"
    if rutas:
        texto += f"Pasan {len(rutas)} ruta(s) por esta parada. Toca una para ver su recorrido:"
    else:
        texto += "Por ahora ninguna ruta pasa por esta parada."
    enlace = mapas.enlace_parada(parada) if mapas.tiene_coordenadas(parada) else None
    await responder(update, texto, teclados.rutas_de_parada(rutas, parada_id, enlace))
