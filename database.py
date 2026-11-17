"""Acceso a la base de datos SQLite: crear tablas, cargar datos de ejemplo y consultas."""

import sqlite3
import unicodedata
from contextlib import contextmanager
from datetime import datetime, timedelta

from config import RUTA_BD
from datos_ejemplo import COORDENADAS, RUTAS

TIPOS_REPORTE = {
    "retraso": "⏰ Retraso",
    "congestion": "🚗 Congestión",
    "lleno": "👥 Bus lleno",
    "mal_estado": "🔧 Vehículo en mal estado",
    "otro": "📝 Otro",
}


def normalizar(texto: str) -> str:
    """Minúsculas y sin tildes, para buscar 'parque berrio' y encontrar 'Parque Berrío'."""
    texto = unicodedata.normalize("NFD", texto.strip().lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


@contextmanager
def conectar():
    """Abre la base, guarda los cambios si todo salió bien y siempre la cierra."""
    conexion = sqlite3.connect(RUTA_BD)
    conexion.row_factory = sqlite3.Row  # permite leer columnas por nombre: fila["nombre"]
    conexion.execute("PRAGMA foreign_keys = ON")
    try:
        yield conexion
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


# ─── Creación de la base de datos ─────────────────────


def inicializar():
    """Crea las tablas si no existen y carga los datos de ejemplo si están vacías."""
    with conectar() as bd:
        bd.executescript(
            """
            CREATE TABLE IF NOT EXISTS rutas (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo      TEXT NOT NULL UNIQUE,
                nombre      TEXT NOT NULL,
                recorrido   TEXT NOT NULL,
                horario     TEXT NOT NULL,
                frecuencia  INTEGER NOT NULL          -- minutos entre buses
            );

            CREATE TABLE IF NOT EXISTS paradas (
                id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre             TEXT NOT NULL UNIQUE,
                nombre_normalizado TEXT NOT NULL,     -- sin tildes, para buscar
                latitud            REAL,
                longitud           REAL
            );

            -- Qué paradas tiene cada ruta y en qué orden
            CREATE TABLE IF NOT EXISTS ruta_parada (
                ruta_id   INTEGER NOT NULL REFERENCES rutas(id),
                parada_id INTEGER NOT NULL REFERENCES paradas(id),
                orden     INTEGER NOT NULL,
                PRIMARY KEY (ruta_id, parada_id)
            );

            CREATE TABLE IF NOT EXISTS reportes (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                ruta_id     INTEGER NOT NULL REFERENCES rutas(id),
                tipo        TEXT NOT NULL,
                descripcion TEXT,
                usuario_id  INTEGER NOT NULL,
                fecha       TEXT NOT NULL
            );
            """
        )
        _agregar_coordenadas(bd)
        hay_rutas = bd.execute("SELECT COUNT(*) FROM rutas").fetchone()[0]
        if not hay_rutas:
            _cargar_datos_ejemplo(bd)
        _completar_coordenadas(bd)


def _agregar_coordenadas(bd):
    """Si la base se creó con la versión anterior (sin mapa), le agrega las columnas."""
    columnas = [fila["name"] for fila in bd.execute("PRAGMA table_info(paradas)")]
    if "latitud" not in columnas:
        bd.execute("ALTER TABLE paradas ADD COLUMN latitud REAL")
        bd.execute("ALTER TABLE paradas ADD COLUMN longitud REAL")


def _completar_coordenadas(bd):
    """Pone las coordenadas de ejemplo a las paradas que todavía no tienen."""
    for nombre, (latitud, longitud) in COORDENADAS.items():
        bd.execute(
            "UPDATE paradas SET latitud = ?, longitud = ? WHERE nombre = ? AND latitud IS NULL",
            (latitud, longitud, nombre),
        )


def _cargar_datos_ejemplo(bd):
    for ruta in RUTAS:
        cursor = bd.execute(
            "INSERT INTO rutas (codigo, nombre, recorrido, horario, frecuencia) VALUES (?, ?, ?, ?, ?)",
            (ruta["codigo"], ruta["nombre"], ruta["recorrido"], ruta["horario"], ruta["frecuencia"]),
        )
        ruta_id = cursor.lastrowid
        for orden, nombre_parada in enumerate(ruta["paradas"], start=1):
            # INSERT OR IGNORE: si la parada ya existe (la comparten varias rutas) no se repite
            bd.execute(
                "INSERT OR IGNORE INTO paradas (nombre, nombre_normalizado) VALUES (?, ?)",
                (nombre_parada, normalizar(nombre_parada)),
            )
            parada_id = bd.execute("SELECT id FROM paradas WHERE nombre = ?", (nombre_parada,)).fetchone()[0]
            bd.execute(
                "INSERT INTO ruta_parada (ruta_id, parada_id, orden) VALUES (?, ?, ?)",
                (ruta_id, parada_id, orden),
            )


# ─── Rutas ────────────────────────────────────────────


def listar_rutas():
    with conectar() as bd:
        return bd.execute("SELECT id, codigo, nombre FROM rutas ORDER BY codigo").fetchall()


def obtener_ruta(ruta_id: int):
    with conectar() as bd:
        return bd.execute("SELECT * FROM rutas WHERE id = ?", (ruta_id,)).fetchone()


def paradas_de_ruta(ruta_id: int):
    with conectar() as bd:
        return bd.execute(
            """SELECT p.id, p.nombre, p.latitud, p.longitud FROM ruta_parada rp
               JOIN paradas p ON p.id = rp.parada_id
               WHERE rp.ruta_id = ? ORDER BY rp.orden""",
            (ruta_id,),
        ).fetchall()


# ─── Paradas ──────────────────────────────────────────


def listar_paradas():
    with conectar() as bd:
        return bd.execute("SELECT id, nombre FROM paradas ORDER BY nombre").fetchall()


def obtener_parada(parada_id: int):
    with conectar() as bd:
        return bd.execute(
            "SELECT id, nombre, latitud, longitud FROM paradas WHERE id = ?", (parada_id,)
        ).fetchone()


def paradas_con_coordenadas():
    with conectar() as bd:
        return bd.execute(
            "SELECT id, nombre, latitud, longitud FROM paradas WHERE latitud IS NOT NULL"
        ).fetchall()


def rutas_de_parada(parada_id: int):
    with conectar() as bd:
        return bd.execute(
            """SELECT r.id, r.codigo, r.nombre FROM ruta_parada rp
               JOIN rutas r ON r.id = rp.ruta_id
               WHERE rp.parada_id = ? ORDER BY r.codigo""",
            (parada_id,),
        ).fetchall()


def buscar_paradas(texto: str):
    """Paradas cuyo nombre contiene el texto (sin importar mayúsculas ni tildes)."""
    with conectar() as bd:
        return bd.execute(
            "SELECT id, nombre FROM paradas WHERE nombre_normalizado LIKE ? ORDER BY nombre",
            (f"%{normalizar(texto)}%",),
        ).fetchall()


# ─── Buscar destino ───────────────────────────────────


def rutas_directas(origen_id: int, destino_id: int):
    """Rutas que pasan por las dos paradas.

    Se asume que los buses hacen el recorrido de ida y vuelta, así que sirve
    cualquier ruta que tenga ambas paradas.
    """
    with conectar() as bd:
        return bd.execute(
            """SELECT r.id, r.codigo, r.nombre FROM rutas r
               JOIN ruta_parada a ON a.ruta_id = r.id AND a.parada_id = ?
               JOIN ruta_parada b ON b.ruta_id = r.id AND b.parada_id = ?
               ORDER BY r.frecuencia""",
            (origen_id, destino_id),
        ).fetchall()


def rutas_con_transbordo(origen_id: int, destino_id: int):
    """Combinaciones de dos rutas: una pasa por el origen, la otra por el destino
    y ambas comparten una parada donde se hace el cambio de bus."""
    with conectar() as bd:
        return bd.execute(
            """SELECT r1.codigo AS ruta1, r1.nombre AS nombre1,
                      p.nombre AS transbordo,
                      r2.codigo AS ruta2, r2.nombre AS nombre2
               FROM ruta_parada o
               JOIN rutas r1 ON r1.id = o.ruta_id
               JOIN ruta_parada t1 ON t1.ruta_id = r1.id
               JOIN ruta_parada t2 ON t2.parada_id = t1.parada_id AND t2.ruta_id <> r1.id
               JOIN rutas r2 ON r2.id = t2.ruta_id
               JOIN ruta_parada d ON d.ruta_id = r2.id AND d.parada_id = ?
               JOIN paradas p ON p.id = t1.parada_id
               WHERE o.parada_id = ?
                 AND t1.parada_id NOT IN (?, ?)
               GROUP BY r1.id, r2.id              -- una sola opción por pareja de rutas
               ORDER BY r1.frecuencia + r2.frecuencia
               LIMIT 5""",
            (destino_id, origen_id, origen_id, destino_id),
        ).fetchall()


# ─── Reportes ─────────────────────────────────────────


def guardar_reporte(ruta_id: int, tipo: str, descripcion: str | None, usuario_id: int) -> int:
    with conectar() as bd:
        cursor = bd.execute(
            "INSERT INTO reportes (ruta_id, tipo, descripcion, usuario_id, fecha) VALUES (?, ?, ?, ?, ?)",
            (ruta_id, tipo, descripcion, usuario_id, datetime.now().isoformat(timespec="minutes")),
        )
        return cursor.lastrowid


def reportes_del_usuario_ultima_hora(usuario_id: int) -> int:
    """Cuántos reportes hizo el usuario en la última hora (para evitar abusos)."""
    desde = (datetime.now() - timedelta(hours=1)).isoformat(timespec="minutes")
    with conectar() as bd:
        return bd.execute(
            "SELECT COUNT(*) FROM reportes WHERE usuario_id = ? AND fecha >= ?", (usuario_id, desde)
        ).fetchone()[0]


def reportes_recientes(ruta_id: int, horas: int = 24):
    """Reportes de una ruta en las últimas horas, del más nuevo al más viejo."""
    desde = (datetime.now() - timedelta(hours=horas)).isoformat(timespec="minutes")
    with conectar() as bd:
        return bd.execute(
            """SELECT tipo, descripcion, fecha FROM reportes
               WHERE ruta_id = ? AND fecha >= ? ORDER BY fecha DESC LIMIT 5""",
            (ruta_id, desde),
        ).fetchall()
