"""Buscar destino: conversación de dos pasos (origen → destino)."""

from html import escape

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

import database
import mapas
import teclados
from handlers.menu import responder
from validaciones import validar_nombre_parada

# Estados de la conversación
ORIGEN, DESTINO = range(2)

PREGUNTAS = {
    "origen": (
        "🔎 <b>Buscar destino</b> (paso 1 de 2)\n\n📍 ¿En qué parada estás? Escribe su nombre o parte de él.\n"
        "<i>Ejemplo: niquia</i>\n\n💡 También puedes enviar tu ubicación (📎 → Ubicación) y uso la parada más cercana."
    ),
    "destino": "🔎 <b>Buscar destino</b> (paso 2 de 2)\n\n🏁 ¿A qué parada quieres llegar?\n<i>Ejemplo: envigado</i>",
}


def lista_de_paradas() -> str:
    nombres = ", ".join(p["nombre"] for p in database.listar_paradas())
    return f"\n\n🚏 Paradas disponibles: <i>{escape(nombres)}</i>"


async def iniciar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["busqueda"] = {}
    await responder(update, PREGUNTAS["origen"], teclados.cancelar())
    return ORIGEN


async def _guardar_parada(update, context, paso: str, parada):
    """Guarda la parada elegida y pasa al siguiente paso (o muestra el resultado)."""
    busqueda = context.user_data.setdefault("busqueda", {})

    if paso == "destino" and parada["id"] == busqueda.get("origen", {}).get("id"):
        await responder(update, "⚠️ El destino es la misma parada de origen. Escribe otra parada.", teclados.cancelar())
        return DESTINO

    busqueda[paso] = {"id": parada["id"], "nombre": parada["nombre"]}
    if paso == "origen":
        await responder(update, f"✅ Origen: <b>{escape(parada['nombre'])}</b>\n\n" + PREGUNTAS["destino"], teclados.cancelar())
        return DESTINO

    await mostrar_resultado(update, busqueda["origen"], busqueda["destino"])
    context.user_data.pop("busqueda", None)
    return ConversationHandler.END


async def _recibir_texto(update: Update, context: ContextTypes.DEFAULT_TYPE, paso: str):
    texto = update.message.text
    error = validar_nombre_parada(texto)
    if error:
        await update.message.reply_text(f"⚠️ {error}", reply_markup=teclados.cancelar(), parse_mode="HTML")
        return ORIGEN if paso == "origen" else DESTINO

    encontradas = database.buscar_paradas(texto)
    estado_actual = ORIGEN if paso == "origen" else DESTINO

    if not encontradas:
        await update.message.reply_text(
            f"😕 No encontré ninguna parada con «{escape(texto.strip())}». Intenta otra vez." + lista_de_paradas(),
            reply_markup=teclados.cancelar(),
            parse_mode="HTML",
        )
        return estado_actual
    if len(encontradas) > 1:
        await update.message.reply_text(
            f"Encontré {len(encontradas)} paradas. ¿Cuál es?",
            reply_markup=teclados.elegir_parada(encontradas[:8]),
        )
        return estado_actual
    return await _guardar_parada(update, context, paso, encontradas[0])


async def recibir_origen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _recibir_texto(update, context, "origen")


async def recibir_destino(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _recibir_texto(update, context, "destino")


async def _recibir_ubicacion(update: Update, context: ContextTypes.DEFAULT_TYPE, paso: str):
    """El usuario envió su ubicación: se usa la parada más cercana."""
    from handlers.ubicacion import paradas_mas_cercanas  # evita importación circular

    ubicacion = update.message.location
    cercanas = paradas_mas_cercanas(ubicacion.latitude, ubicacion.longitude, cuantas=1)
    if not cercanas:
        await update.message.reply_text("No hay paradas con ubicación registrada. Escribe el nombre.")
        return ORIGEN if paso == "origen" else DESTINO
    parada = cercanas[0]
    await update.message.reply_text(f"📍 Parada más cercana: {parada['nombre']} ({parada['distancia']}).")
    return await _guardar_parada(update, context, paso, parada)


async def ubicacion_origen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _recibir_ubicacion(update, context, "origen")


async def ubicacion_destino(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _recibir_ubicacion(update, context, "destino")


async def _elegir(update: Update, context: ContextTypes.DEFAULT_TYPE, paso: str):
    """El usuario tocó una de las paradas sugeridas."""
    try:
        parada = database.obtener_parada(int(update.callback_query.data.split(":")[1]))
    except (IndexError, ValueError):
        parada = None
    if not parada:
        await responder(update, "⚠️ No encontré esa parada. Escríbela de nuevo.", teclados.cancelar())
        return ORIGEN if paso == "origen" else DESTINO
    return await _guardar_parada(update, context, paso, parada)


async def elegir_origen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _elegir(update, context, "origen")


async def elegir_destino(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _elegir(update, context, "destino")


async def mostrar_resultado(update: Update, origen: dict, destino: dict):
    texto = f"🔎 <b>{escape(origen['nombre'])} → {escape(destino['nombre'])}</b>\n\n"
    enlace = mapas.enlace_como_llegar(database.obtener_parada(origen["id"]), database.obtener_parada(destino["id"]))

    directas = database.rutas_directas(origen["id"], destino["id"])
    if directas:
        texto += "✅ <b>Rutas directas:</b>\n"
        texto += "\n".join(f"  🚌 {r['codigo']} · {escape(r['nombre'])}" for r in directas)
        await responder(update, texto, teclados.resultado_busqueda(directas, enlace))
        return

    combinaciones = database.rutas_con_transbordo(origen["id"], destino["id"])
    if combinaciones:
        texto += "No hay ruta directa, pero puedes llegar con <b>un transbordo</b>:\n"
        for c in combinaciones:
            texto += (
                f"\n  1️⃣ Toma la <b>{c['ruta1']}</b> ({escape(c['nombre1'])}) hasta <b>{escape(c['transbordo'])}</b>"
                f"\n  2️⃣ Allí cambia a la <b>{c['ruta2']}</b> ({escape(c['nombre2'])})\n"
            )
        await responder(update, texto, teclados.resultado_busqueda([], enlace))
        return

    texto += "😕 No encontré rutas directas ni con un transbordo entre esas paradas."
    await responder(update, texto, teclados.resultado_busqueda([], enlace))
