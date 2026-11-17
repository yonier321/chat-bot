"""Mapas: ver una parada en el mapa y encontrar la parada más cercana a tu ubicación."""

from html import escape

from telegram import ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes

import database
import mapas
import teclados
from handlers.menu import responder

CUANTAS_CERCANAS = 3


def paradas_mas_cercanas(latitud: float, longitud: float, cuantas: int = CUANTAS_CERCANAS):
    """Ordena las paradas por distancia a un punto y devuelve las más cercanas."""
    paradas = []
    for p in database.paradas_con_coordenadas():
        metros = mapas.distancia_metros(latitud, longitud, p["latitud"], p["longitud"])
        paradas.append({**dict(p), "metros": metros, "distancia": mapas.formatear_distancia(metros)})
    paradas.sort(key=lambda p: p["metros"])
    return paradas[:cuantas]


async def ver_ubicacion_parada(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Envía la parada como un punto en el mapa de Telegram (botón 'Ver en el mapa')."""
    consulta = update.callback_query
    await consulta.answer()
    try:
        parada = database.obtener_parada(int(consulta.data.split(":")[1]))
    except (IndexError, ValueError):
        parada = None
    if not mapas.tiene_coordenadas(parada):
        await consulta.message.reply_text("⚠️ Esta parada no tiene ubicación registrada.")
        return

    rutas = ", ".join(r["codigo"] for r in database.rutas_de_parada(parada["id"])) or "ninguna"
    # send_venue muestra un mapa con el nombre del lugar; al tocarlo se abre en el mapa del celular
    await consulta.message.reply_venue(
        latitude=parada["latitud"],
        longitude=parada["longitud"],
        title=f"🚏 {parada['nombre']}",
        address=f"Rutas que pasan: {rutas}",
        reply_markup=teclados.volver_parada(parada["id"]),
    )


async def pedir_ubicacion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Botón 'Parada más cercana' o /cercana: pide la ubicación del usuario."""
    if update.callback_query:
        await update.callback_query.answer()
    await update.effective_message.reply_text(
        "📍 <b>Parada más cercana</b>\n\n"
        "Toca el botón <b>«📍 Enviar mi ubicación»</b> que aparece abajo.\n\n"
        "<i>Desde el computador ese botón no aparece: abre el bot en el celular "
        "o envía una ubicación con 📎 → Ubicación.</i>",
        reply_markup=teclados.pedir_ubicacion(),
        parse_mode="HTML",
    )


async def recibir_ubicacion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """El usuario envió su ubicación: se le muestran las paradas más cercanas."""
    ubicacion = update.message.location
    cercanas = paradas_mas_cercanas(ubicacion.latitude, ubicacion.longitude)
    if not cercanas:
        await update.message.reply_text("No hay paradas con ubicación registrada.", reply_markup=ReplyKeyboardRemove())
        return

    # Quita el teclado de "Enviar mi ubicación" que quedó abajo
    await update.message.reply_text("🔎 Buscando paradas cerca de ti...", reply_markup=ReplyKeyboardRemove())

    mas_cercana = cercanas[0]
    texto = (
        f"📍 <b>Paradas más cercanas</b>\n\n"
        f"La más cercana es <b>{escape(mas_cercana['nombre'])}</b>, a {mas_cercana['distancia']} en línea recta.\n\n"
        "Toca una parada para ver qué rutas pasan:"
    )
    if mas_cercana["metros"] > 5000:
        texto += "\n\n⚠️ Estás lejos de todas las paradas registradas."

    enlace = (
        "https://www.google.com/maps/dir/?api=1"
        f"&origin={ubicacion.latitude},{ubicacion.longitude}"
        f"&destination={mas_cercana['latitud']},{mas_cercana['longitud']}&travelmode=walking"
    )
    await responder(update, texto, teclados.paradas_cercanas(cercanas, enlace))
