"""/start, /ayuda, menú principal y respuesta común para botones y mensajes."""

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler

import teclados

BIENVENIDA = (
    "👋 ¡Hola, {nombre}! Soy <b>MoviBot</b>, tu asistente de transporte público.\n\n"
    "Puedo ayudarte a:\n"
    "🚌 Ver las rutas y sus paradas\n"
    "🚏 Saber qué rutas pasan por una parada\n"
    "🔎 Encontrar cómo llegar a tu destino\n"
    "📍 Encontrar la parada más cercana\n"
    "⚠️ Reportar retrasos o problemas\n\n"
    "Elige una opción 👇"
)

AYUDA = (
    "❓ <b>Cómo usar el bot</b>\n\n"
    "🚌 <b>Rutas:</b> muestra todas las rutas. Toca una para ver su recorrido, horario, "
    "frecuencia, paradas y los problemas reportados hoy.\n\n"
    "🚏 <b>Paradas:</b> toca una parada para ver qué rutas pasan por ella.\n\n"
    "🔎 <b>Buscar destino:</b> escribe dónde estás y a dónde vas (basta con parte del nombre, "
    "por ejemplo <i>berrio</i>), o envía tu ubicación. Te muestro las rutas directas o con un "
    "transbordo, y un enlace para verlo en Google Maps.\n\n"
    "📍 <b>Parada más cercana:</b> envía tu ubicación desde el celular y te digo qué paradas "
    "tienes cerca.\n\n"
    "🗺️ <b>Mapas:</b> en cada parada puedes verla en el mapa, y en cada ruta ver su recorrido "
    "en Google Maps.\n\n"
    "⚠️ <b>Reportar problema:</b> elige la ruta y el tipo de problema, y si quieres agrega "
    "una descripción.\n\n"
    "<b>Comandos:</b>\n"
    "/start – menú principal\n"
    "/rutas – lista de rutas\n"
    "/paradas – lista de paradas\n"
    "/buscar – buscar destino\n"
    "/cercana – parada más cercana\n"
    "/reportar – reportar un problema\n"
    "/cancelar – cancelar la acción actual\n"
    "/ayuda – esta ayuda"
)


async def responder(update: Update, texto: str, teclado=None):
    """Si el usuario pulsó un botón, edita ese mensaje; si escribió, envía uno nuevo.

    Editar el mensaje evita que el chat se llene de menús repetidos.
    """
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            texto, reply_markup=teclado, parse_mode=ParseMode.HTML
        )
    else:
        await update.effective_message.reply_text(texto, reply_markup=teclado, parse_mode=ParseMode.HTML)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()  # olvida cualquier búsqueda o reporte a medias
    nombre = update.effective_user.first_name or "viajero"
    await responder(update, BIENVENIDA.format(nombre=nombre), teclados.menu_principal())
    return ConversationHandler.END


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await responder(update, "🏠 <b>Menú principal</b>\n¿Qué quieres hacer?", teclados.menu_principal())
    return ConversationHandler.END


async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await responder(update, AYUDA, teclados.volver_menu())


async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sale de la búsqueda o del reporte en curso y vuelve al menú."""
    context.user_data.clear()
    await responder(update, "✖️ Acción cancelada.\n\n🏠 <b>Menú principal</b>", teclados.menu_principal())
    return ConversationHandler.END


async def mensaje_no_entendido(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Texto que llega fuera de una búsqueda o un reporte."""
    await update.message.reply_text(
        "🤔 No entendí ese mensaje. Usa los botones del menú 👇",
        reply_markup=teclados.menu_principal(),
    )
