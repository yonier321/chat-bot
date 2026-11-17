"""Configuración del bot: lee el token desde el archivo .env o las variables de entorno."""

import os
import sys

from dotenv import load_dotenv

load_dotenv()  # carga las variables del archivo .env si existe

TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
RUTA_BD = os.getenv("RUTA_BD", "transporte.db")


def validar_configuracion():
    """Detiene el programa con un mensaje claro si falta el token."""
    if not TOKEN or TOKEN == "pega_aqui_tu_token":
        print("❌ Falta el token del bot.")
        print("   1. Copia .env.example como .env")
        print("   2. Pega en TELEGRAM_TOKEN el token que te dio @BotFather")
        sys.exit(1)
