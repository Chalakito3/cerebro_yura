#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Registro de resultados de Yura en SQLite (resultados.db).

Cada intento del juego y de la práctica se guarda con la palabra, lo que
respondió el estudiante, si acertó, la fecha y el estudiante o grupo que el
docente indicó en la página de resultados. El diccionario (diccionario.db)
no se modifica: los resultados viven en su propio archivo.

Registrar un resultado nunca debe detener a Yura: cualquier error se
informa en el registro y se ignora.
"""

import os
import re
import sqlite3
import uuid
from datetime import datetime

RUTA_DB = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "resultados.db"
)

ACTIVIDADES = ("juego", "practica")
SIN_PARTICIPANTE = ""
LARGO_MAXIMO_PARTICIPANTE = 40

_ESQUEMA = """
CREATE TABLE IF NOT EXISTS intentos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha           TEXT    NOT NULL,
    actividad       TEXT    NOT NULL CHECK (actividad IN ('juego', 'practica')),
    sesion          TEXT    NOT NULL,
    palabra_espanol TEXT    NOT NULL,
    palabra_quechua TEXT    NOT NULL,
    respuesta       TEXT    NOT NULL DEFAULT '',
    correcto        INTEGER NOT NULL CHECK (correcto IN (0, 1)),
    participante    TEXT    NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS configuracion (
    clave TEXT PRIMARY KEY,
    valor TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_intentos_fecha ON intentos (fecha);
CREATE INDEX IF NOT EXISTS idx_intentos_sesion ON intentos (sesion);
"""


def _conectar():
    conexion = sqlite3.connect(RUTA_DB, timeout=5)
    conexion.row_factory = sqlite3.Row
    conexion.executescript(_ESQUEMA)
    columnas = [fila[1] for fila in conexion.execute("PRAGMA table_info(intentos)")]
    if "participante" not in columnas:
        # Bases creadas antes de registrar estudiantes o grupos.
        conexion.execute("ALTER TABLE intentos ADD COLUMN participante TEXT NOT NULL DEFAULT ''")
    conexion.execute("CREATE INDEX IF NOT EXISTS idx_intentos_participante ON intentos (participante)")
    return conexion


def nueva_sesion():
    """Identificador de una partida del juego o de una práctica."""
    return uuid.uuid4().hex[:12]


def limpiar_participante(nombre):
    """Nombre corto y seguro: letras (con tildes y ñ), números, espacios,
    punto, guion y el signo de número. Sirve para grupos ("Grupo 2") o
    números de lista ("N.º 14")."""
    nombre = re.sub(r"[^\w .\-º°#']", "", str(nombre or ""), flags=re.UNICODE)
    nombre = re.sub(r"\s+", " ", nombre).strip()
    return nombre[:LARGO_MAXIMO_PARTICIPANTE]


def participante_actual():
    try:
        with _conectar() as conexion:
            fila = conexion.execute(
                "SELECT valor FROM configuracion WHERE clave = 'participante_actual'"
            ).fetchone()
        return fila["valor"] if fila else SIN_PARTICIPANTE
    except Exception as exc:
        print(f"[RESULTADOS] No se pudo leer el participante: {exc}")
        return SIN_PARTICIPANTE


def definir_participante(nombre):
    """Guarda quién está jugando ahora; los intentos siguientes se registran
    a su nombre. Un nombre vacío vuelve a "sin nombre"."""
    nombre = limpiar_participante(nombre)
    with _conectar() as conexion:
        conexion.execute(
            "INSERT INTO configuracion (clave, valor) VALUES ('participante_actual', ?) "
            "ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor",
            (nombre,),
        )
    return nombre


def registrar_intento(actividad, palabra_espanol, palabra_quechua, respuesta,
                      correcto, sesion, participante=None):
    if actividad not in ACTIVIDADES:
        print(f"[RESULTADOS] Actividad desconocida: {actividad}")
        return False
    try:
        if participante is None:
            participante = participante_actual()
        with _conectar() as conexion:
            conexion.execute(
                """
                INSERT INTO intentos (
                    fecha, actividad, sesion, palabra_espanol,
                    palabra_quechua, respuesta, correcto, participante
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now().isoformat(timespec="seconds"),
                    actividad,
                    str(sesion or "sin-sesion"),
                    str(palabra_espanol or "").strip()[:120],
                    str(palabra_quechua or "").strip()[:120],
                    str(respuesta or "").strip()[:300],
                    1 if correcto else 0,
                    limpiar_participante(participante),
                ),
            )
        return True
    except Exception as exc:
        print(f"[RESULTADOS] No se pudo guardar el intento: {exc}")
        return False


def _porcentaje(aciertos, total):
    return round(100 * aciertos / total) if total else 0


def resumen(limite_intentos=50, participante=None):
    """Datos para la página de resultados. Con participante, solo los de
    ese estudiante o grupo."""
    filtro, parametros = "", ()
    if participante is not None:
        filtro, parametros = "WHERE participante = ?", (participante,)

    with _conectar() as conexion:
        total, aciertos = conexion.execute(
            f"SELECT COUNT(*), COALESCE(SUM(correcto), 0) FROM intentos {filtro}",
            parametros,
        ).fetchone()

        por_actividad = []
        for fila in conexion.execute(
            f"""
            SELECT actividad, COUNT(*) AS total, SUM(correcto) AS aciertos,
                   COUNT(DISTINCT sesion) AS sesiones
            FROM intentos {filtro} GROUP BY actividad ORDER BY actividad
            """,
            parametros,
        ):
            por_actividad.append({
                "actividad": fila["actividad"],
                "total": fila["total"],
                "aciertos": fila["aciertos"],
                "sesiones": fila["sesiones"],
                "porcentaje": _porcentaje(fila["aciertos"], fila["total"]),
            })

        por_participante = [
            {
                "participante": fila["participante"],
                "total": fila["total"],
                "aciertos": fila["aciertos"],
                "porcentaje": _porcentaje(fila["aciertos"], fila["total"]),
                "ultima_fecha": fila["ultima_fecha"],
            }
            for fila in conexion.execute(
                """
                SELECT participante, COUNT(*) AS total, SUM(correcto) AS aciertos,
                       MAX(fecha) AS ultima_fecha
                FROM intentos GROUP BY participante ORDER BY ultima_fecha DESC
                """
            )
        ]

        palabras_dificiles = [
            {
                "espanol": fila["palabra_espanol"],
                "quechua": fila["palabra_quechua"],
                "intentos": fila["intentos"],
                "fallos": fila["fallos"],
                "porcentaje": _porcentaje(fila["intentos"] - fila["fallos"], fila["intentos"]),
            }
            for fila in conexion.execute(
                f"""
                SELECT palabra_espanol, palabra_quechua, COUNT(*) AS intentos,
                       COUNT(*) - SUM(correcto) AS fallos
                FROM intentos {filtro}
                GROUP BY palabra_espanol, palabra_quechua
                HAVING fallos > 0
                ORDER BY fallos DESC, intentos DESC
                LIMIT 10
                """,
                parametros,
            )
        ]

        por_dia = [
            {
                "dia": fila["dia"],
                "total": fila["total"],
                "aciertos": fila["aciertos"],
                "porcentaje": _porcentaje(fila["aciertos"], fila["total"]),
            }
            for fila in conexion.execute(
                f"""
                SELECT substr(fecha, 1, 10) AS dia, COUNT(*) AS total,
                       SUM(correcto) AS aciertos
                FROM intentos {filtro} GROUP BY dia ORDER BY dia DESC LIMIT 14
                """,
                parametros,
            )
        ]

        ultimos = [
            dict(fila)
            for fila in conexion.execute(
                f"""
                SELECT fecha, actividad, palabra_espanol, palabra_quechua,
                       respuesta, correcto, participante
                FROM intentos {filtro} ORDER BY id DESC LIMIT ?
                """,
                parametros + (int(limite_intentos),),
            )
        ]

    return {
        "total": total,
        "aciertos": aciertos,
        "porcentaje": _porcentaje(aciertos, total),
        "por_actividad": por_actividad,
        "por_participante": por_participante,
        "palabras_dificiles": palabras_dificiles,
        "por_dia": por_dia,
        "ultimos": ultimos,
        "filtro_participante": participante,
        "participante_actual": participante_actual(),
    }


def todos_los_intentos():
    """Todos los intentos, del más antiguo al más reciente (para exportar)."""
    with _conectar() as conexion:
        return [
            dict(fila)
            for fila in conexion.execute(
                """
                SELECT id, fecha, actividad, sesion, participante, palabra_espanol,
                       palabra_quechua, respuesta, correcto
                FROM intentos ORDER BY id
                """
            )
        ]
