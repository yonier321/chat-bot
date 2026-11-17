"""Punto de entrada: crea el bot, registra los comandos y botones, y lo pone a funcionar.

Ejecutar:  python bot.py
"""

import logging

from telegram import BotCommand, Update
from telegram.error import BadRequest
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

import database
import teclados
from config import TOKEN, validar_configuracion
from handlers import buscar, menu, reportes, ubicacion
from handlers.rutas_paradas import detalle_parada, detalle_ruta, listar_paradas, listar_rutas

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)  # oculta el registro de cada petición
log = logging.getLogger("movibot")

SOLO_TEXTO = filters.TEXT & ~filters.COMMAND


def salir_y(funcion):
    """Para usar dentro de una conversación: ejecuta la acción y termina la conversación.

    Así, si el usuario está buscando un destino y toca 'Rutas', no queda atrapado.
    """
    async def envoltura(update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data.clear()
        await funcion(update, context)
        return ConversationHandler.END

    return envoltura


def navegacion(dentro_de_conversacion=False):
    """Comandos y botones del menú, que funcionan en cualquier momento.

    Dentro de una conversación se envuelven con salir_y() para que, además de
    mostrar lo pedido, cierren la búsqueda o el reporte que estaba a medias.
    """
    envolver = salir_y if dentro_de_conversacion else (lambda funcion: funcion)
    return [
        CommandHandler("start", envolver(menu.start)),
        CommandHandler("ayuda", envolver(menu.ayuda)),
        CommandHandler("rutas", envolver(listar_rutas)),
        CommandHandler("paradas", envolver(listar_paradas)),
        CallbackQueryHandler(envolver(menu.menu), pattern=r"^menu$"),
        CallbackQueryHandler(envolver(menu.ayuda), pattern=r"^ayuda$"),
        CallbackQueryHandler(envolver(listar_rutas), pattern=r"^rutas$"),
        CallbackQueryHandler(envolver(detalle_ruta), pattern=r"^ruta:\d+$"),
        CallbackQueryHandler(envolver(listar_paradas), pattern=r"^paradas$"),
        CallbackQueryHandler(envolver(detalle_parada), pattern=r"^parada:\d+$"),
        CommandHandler("cercana", envolver(ubicacion.pedir_ubicacion)),
        CallbackQueryHandler(envolver(ubicacion.pedir_ubicacion), pattern=r"^cercana$"),
        CallbackQueryHandler(ubicacion.ver_ubicacion_parada, pattern=r"^ubicacion:\d+$"),
    ]


def salidas_de_conversacion():
    """Fallbacks: /cancelar, el botón Cancelar o cualquier opción del menú cierran la conversación."""
    return [
        CommandHandler("cancelar", menu.cancelar),
        CallbackQueryHandler(menu.cancelar, pattern=r"^cancelar$"),
        *navegacion(dentro_de_conversacion=True),
    ]


def crear_conversaciones():
    conversacion_buscar = ConversationHandler(
        entry_points=[
            CommandHandler("buscar", buscar.iniciar),
            CallbackQueryHandler(buscar.iniciar, pattern=r"^buscar$"),
        ],
        states={
            buscar.ORIGEN: [
                MessageHandler(SOLO_TEXTO, buscar.recibir_origen),
                MessageHandler(filters.LOCATION, buscar.ubicacion_origen),
                CallbackQueryHandler(buscar.elegir_origen, pattern=r"^elegir:\d+$"),
            ],
            buscar.DESTINO: [
                MessageHandler(SOLO_TEXTO, buscar.recibir_destino),
                MessageHandler(filters.LOCATION, buscar.ubicacion_destino),
                CallbackQueryHandler(buscar.elegir_destino, pattern=r"^elegir:\d+$"),
            ],
        },
        fallbacks=salidas_de_conversacion(),
        allow_reentry=True,  # tocar "Buscar destino" otra vez empieza de nuevo
    )

    conversacion_reportar = ConversationHandler(
        entry_points=[
            CommandHandler("reportar", reportes.iniciar),
            CallbackQueryHandler(reportes.iniciar, pattern=r"^reportar(:\d+)?$"),
        ],
        states={
            reportes.ELEGIR_RUTA: [CallbackQueryHandler(reportes.elegir_ruta, pattern=r"^rep_ruta:\d+$")],
            reportes.ELEGIR_TIPO: [CallbackQueryHandler(reportes.elegir_tipo, pattern=r"^rep_tipo:\w+$")],
            reportes.DESCRIPCION: [
                MessageHandler(SOLO_TEXTO, reportes.recibir_descripcion),
                CallbackQueryHandler(reportes.omitir_descripcion, pattern=r"^rep_omitir$"),
            ],
        },
        fallbacks=salidas_de_conversacion(),
        allow_reentry=True,
    )
    return conversacion_buscar, conversacion_reportar


async def manejar_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Registra cualquier error y avisa al usuario en vez de quedarse callado."""
    error = context.error
    if isinstance(error, BadRequest) and "message is not modified" in str(error).lower():
        return  # el usuario tocó dos veces el mismo botón: no es un problema
    log.error("Error atendiendo un mensaje", exc_info=error)
    if isinstance(update, Update) and update.effective_chat:
        await context.bot.send_message(
            update.effective_chat.id,
            "😓 Ocurrió un error inesperado. Intenta de nuevo o escribe /start.",
            reply_markup=teclados.volver_menu(),
        )


async def configurar_menu_de_comandos(app: Application):
    """Lista de comandos que Telegram muestra al escribir '/'."""
    await app.bot.set_my_commands([
        BotCommand("start", "Menú principal"),
        BotCommand("rutas", "Ver las rutas"),
        BotCommand("paradas", "Ver las paradas"),
        BotCommand("buscar", "Buscar cómo llegar a un destino"),
        BotCommand("cercana", "Parada más cercana a tu ubicación"),
        BotCommand("reportar", "Reportar un problema en una ruta"),
        BotCommand("cancelar", "Cancelar la acción actual"),
        BotCommand("ayuda", "Cómo usar el bot"),
    ])


def crear_aplicacion() -> Application:
    app = ApplicationBuilder().token(TOKEN).post_init(configurar_menu_de_comandos).build()
    # Las conversaciones van primero para que capturen el texto que esperan
    for conversacion in crear_conversaciones():
        app.add_handler(conversacion)
    for handler in navegacion():
        app.add_handler(handler)
    app.add_handler(CommandHandler("cancelar", menu.cancelar))
    app.add_handler(CallbackQueryHandler(menu.cancelar, pattern=r"^cancelar$"))
    app.add_handler(MessageHandler(filters.LOCATION, ubicacion.recibir_ubicacion))
    app.add_handler(MessageHandler(SOLO_TEXTO, menu.mensaje_no_entendido))
    app.add_error_handler(manejar_error)
    return app


def main():
    validar_configuracion()
    database.inicializar()
    log.info("Base de datos lista. Iniciando el bot... (Ctrl+C para detener)")
    crear_aplicacion().run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
