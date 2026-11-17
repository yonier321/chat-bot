"""Reportar problemas: conversación de tres pasos (ruta → tipo → descripción)."""

from html import escape

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

import database
import teclados
from database import TIPOS_REPORTE
from handlers.menu import responder
from validaciones import validar_descripcion

# Estados de la conversación
ELEGIR_RUTA, ELEGIR_TIPO, DESCRIPCION = range(3)

MAXIMO_POR_HORA = 5  # evita que una misma persona llene la base con reportes


async def iniciar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entrada desde el menú o /reportar. Si viene de 'reportar:3' la ruta ya está elegida."""
    if database.reportes_del_usuario_ultima_hora(update.effective_user.id) >= MAXIMO_POR_HORA:
        await responder(
            update,
            f"⏳ Ya enviaste {MAXIMO_POR_HORA} reportes en la última hora. Intenta más tarde.",
            teclados.volver_menu(),
        )
        return ConversationHandler.END

    context.user_data["reporte"] = {}
    datos = update.callback_query.data if update.callback_query else ""
    if datos.startswith("reportar:"):
        return await _guardar_ruta(update, context, datos.split(":")[1])

    rutas = database.listar_rutas()
    await responder(
        update,
        "⚠️ <b>Reportar problema</b> (paso 1 de 3)\n\n¿En qué ruta se presenta el problema?",
        teclados.lista(rutas, "rep_ruta", lambda r: f"{r['codigo']} · {r['nombre']}", volver="cancelar"),
    )
    return ELEGIR_RUTA


async def _guardar_ruta(update, context, valor: str):
    ruta = database.obtener_ruta(int(valor)) if valor.isdigit() else None
    if not ruta:
        await responder(update, "⚠️ Esa ruta no existe. Empieza de nuevo.", teclados.volver_menu())
        return ConversationHandler.END
    context.user_data.setdefault("reporte", {})["ruta"] = {"id": ruta["id"], "nombre": f"{ruta['codigo']} · {ruta['nombre']}"}
    await responder(
        update,
        f"⚠️ <b>Reportar problema</b> (paso 2 de 3)\n\nRuta: <b>{escape(ruta['codigo'])} · {escape(ruta['nombre'])}</b>\n\n¿Qué tipo de problema es?",
        teclados.tipos_reporte(),
    )
    return ELEGIR_TIPO


async def elegir_ruta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _guardar_ruta(update, context, update.callback_query.data.split(":")[1])


async def elegir_tipo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tipo = update.callback_query.data.split(":")[1]
    reporte = context.user_data.get("reporte", {})
    if tipo not in TIPOS_REPORTE or "ruta" not in reporte:
        await responder(update, "⚠️ Opción no válida. Empieza de nuevo.", teclados.volver_menu())
        return ConversationHandler.END
    reporte["tipo"] = tipo
    await responder(
        update,
        f"⚠️ <b>Reportar problema</b> (paso 3 de 3)\n\n{TIPOS_REPORTE[tipo]} en <b>{escape(reporte['ruta']['nombre'])}</b>\n\n"
        "✍️ Describe brevemente lo que pasa (dónde, desde qué hora...).\n<i>Entre 5 y 300 caracteres.</i>",
        teclados.omitir_descripcion(),
    )
    return DESCRIPCION


async def recibir_descripcion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    error = validar_descripcion(update.message.text)
    if error:
        await update.message.reply_text(f"⚠️ {error}", reply_markup=teclados.omitir_descripcion())
        return DESCRIPCION
    return await _guardar(update, context, update.message.text.strip())


async def omitir_descripcion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _guardar(update, context, None)


async def _guardar(update, context, descripcion):
    reporte = context.user_data.pop("reporte", {})
    if "ruta" not in reporte or "tipo" not in reporte:
        await responder(update, "⚠️ Se perdió el reporte. Empieza de nuevo.", teclados.volver_menu())
        return ConversationHandler.END

    numero = database.guardar_reporte(reporte["ruta"]["id"], reporte["tipo"], descripcion, update.effective_user.id)
    await responder(
        update,
        f"✅ <b>Reporte #{numero} registrado.</b> ¡Gracias por avisar!\n\n"
        f"🚌 {escape(reporte['ruta']['nombre'])}\n{TIPOS_REPORTE[reporte['tipo']]}"
        + (f"\n📝 {escape(descripcion)}" if descripcion else "")
        + "\n\nOtros usuarios lo verán en el detalle de la ruta durante 24 horas.",
        teclados.detalle_ruta(reporte["ruta"]["id"]),
    )
    return ConversationHandler.END
