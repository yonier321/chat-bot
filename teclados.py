"""Botones interactivos (InlineKeyboard) que usa el bot.

Cada botón tiene un callback_data: un texto corto que el bot recibe cuando lo pulsan.
Ejemplos: "rutas", "ruta:3", "parada:7", "rep_tipo:retraso".
"""

from telegram import InlineKeyboardButton as Boton
from telegram import InlineKeyboardMarkup as Teclado
from telegram import KeyboardButton, ReplyKeyboardMarkup

from database import TIPOS_REPORTE


def menu_principal():
    return Teclado([
        [Boton("🚌 Rutas", callback_data="rutas"), Boton("🚏 Paradas", callback_data="paradas")],
        [Boton("🔎 Buscar destino", callback_data="buscar")],
        [Boton("📍 Parada más cercana", callback_data="cercana")],
        [Boton("⚠️ Reportar problema", callback_data="reportar")],
        [Boton("❓ Ayuda", callback_data="ayuda")],
    ])


def volver_menu():
    return Teclado([[Boton("🏠 Menú principal", callback_data="menu")]])


def cancelar():
    return Teclado([[Boton("✖️ Cancelar", callback_data="cancelar")]])


def lista(elementos, prefijo, texto_de, volver="menu", columnas=1):
    """Un botón por elemento (ruta, parada...) y al final el botón para volver."""
    botones = [Boton(texto_de(e), callback_data=f"{prefijo}:{e['id']}") for e in elementos]
    filas = [botones[i:i + columnas] for i in range(0, len(botones), columnas)]
    filas.append([Boton("🔙 Volver", callback_data=volver)])
    return Teclado(filas)


def detalle_ruta(ruta_id, enlace_mapa=None):
    filas = []
    if enlace_mapa:
        # Botón con url: abre Google Maps en vez de enviarle algo al bot
        filas.append([Boton("🗺️ Ver recorrido en Google Maps", url=enlace_mapa)])
    filas.append([Boton("⚠️ Reportar problema en esta ruta", callback_data=f"reportar:{ruta_id}")])
    filas.append([Boton("🔙 Rutas", callback_data="rutas"), Boton("🏠 Menú", callback_data="menu")])
    return Teclado(filas)


def rutas_de_parada(rutas, parada_id=None, enlace_mapa=None):
    filas = [[Boton(f"🚌 {r['codigo']} · {r['nombre']}", callback_data=f"ruta:{r['id']}")] for r in rutas]
    if enlace_mapa:
        filas.append([
            Boton("📍 Ver en el mapa", callback_data=f"ubicacion:{parada_id}"),
            Boton("🗺️ Google Maps", url=enlace_mapa),
        ])
    filas.append([Boton("🔙 Paradas", callback_data="paradas"), Boton("🏠 Menú", callback_data="menu")])
    return Teclado(filas)


def volver_parada(parada_id):
    return Teclado([[Boton("🔙 Volver a la parada", callback_data=f"parada:{parada_id}"), Boton("🏠 Menú", callback_data="menu")]])


def pedir_ubicacion():
    """Teclado especial (debajo del chat) con un botón que envía la ubicación del celular."""
    return ReplyKeyboardMarkup(
        [[KeyboardButton("📍 Enviar mi ubicación", request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def paradas_cercanas(paradas, enlace_caminando=None):
    filas = [[Boton(f"🚏 {p['nombre']} ({p['distancia']})", callback_data=f"parada:{p['id']}")] for p in paradas]
    if enlace_caminando:
        filas.append([Boton("🚶 Cómo llegar caminando", url=enlace_caminando)])
    filas.append([Boton("🏠 Menú", callback_data="menu")])
    return Teclado(filas)


def elegir_parada(paradas):
    """Cuando lo escrito coincide con varias paradas, el usuario elige la correcta."""
    filas = [[Boton(f"🚏 {p['nombre']}", callback_data=f"elegir:{p['id']}")] for p in paradas]
    filas.append([Boton("✖️ Cancelar", callback_data="cancelar")])
    return Teclado(filas)


def resultado_busqueda(rutas, enlace_mapa=None):
    filas = [[Boton(f"Ver {r['codigo']} · {r['nombre']}", callback_data=f"ruta:{r['id']}")] for r in rutas]
    if enlace_mapa:
        filas.append([Boton("🗺️ Cómo llegar en Google Maps", url=enlace_mapa)])
    filas.append([Boton("🔎 Nueva búsqueda", callback_data="buscar"), Boton("🏠 Menú", callback_data="menu")])
    return Teclado(filas)


def tipos_reporte():
    filas = [[Boton(texto, callback_data=f"rep_tipo:{clave}")] for clave, texto in TIPOS_REPORTE.items()]
    filas.append([Boton("✖️ Cancelar", callback_data="cancelar")])
    return Teclado(filas)


def omitir_descripcion():
    return Teclado([
        [Boton("⏭️ Enviar sin descripción", callback_data="rep_omitir")],
        [Boton("✖️ Cancelar", callback_data="cancelar")],
    ])
