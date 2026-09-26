#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import unicodedata


_IDIOMAS_ENTRADA = {"espanol", "quechua"}
_TABLA_VOCABULARIO = re.compile(r"^nivel(?P<nivel>\d+)_(?P<categoria>[a-z0-9_]+)$")


def _identificador_sql(nombre):
    """Cita un identificador obtenido del esquema SQLite, no del usuario."""
    return '"' + str(nombre).replace('"', '""') + '"'


def _normalizar_texto(texto):
    if texto is None:
        return ""

    try:
        texto = str(texto).strip()
    except Exception:
        return ""

    if texto == "":
        return ""

    texto = texto.lower()

    texto = (
        texto
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("ü", "u")
    )

    texto = re.sub(r"[^a-z0-9\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


def _normalizar_para_comparar(texto):
    if texto is None:
        return ""

    texto = str(texto).strip().lower().replace("’", "'")
    texto = texto.replace("ñ", "\x00")
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(
        caracter
        for caracter in texto
        if not unicodedata.combining(caracter)
    )
    texto = texto.replace("\x00", "ñ")
    texto = re.sub(r"[^a-z0-9ñ'\-\s]", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def _tablas_de_vocabulario(conexion_db):
    cursor = conexion_db.cursor()
    cursor.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    )

    tablas = []
    for (nombre_tabla,) in cursor.fetchall():
        coincidencia = _TABLA_VOCABULARIO.fullmatch(str(nombre_tabla))
        if coincidencia is None:
            continue

        cursor.execute(
            f"PRAGMA table_info({_identificador_sql(nombre_tabla)})"
        )
        columnas = {str(fila[1]) for fila in cursor.fetchall()}
        if {"id", "palabra_frase", "traduccion", "pronunciacion"}.issubset(columnas):
            tablas.append((
                nombre_tabla,
                int(coincidencia.group("nivel")),
                coincidencia.group("categoria")
            ))

    return tablas


def _leer_registros_vocabulario(conexion_db):
    registros = []

    for nombre_tabla, nivel, categoria in _tablas_de_vocabulario(conexion_db):
        tabla_sql = _identificador_sql(nombre_tabla)
        columnas = (
            "id, palabra_frase, traduccion, pronunciacion, significado"
        )

        try:
            cursor = conexion_db.cursor()
            cursor.execute(
                f"SELECT {columnas} FROM {tabla_sql} ORDER BY id"
            )
        except Exception:
            cursor = conexion_db.cursor()
            cursor.execute(
                f"SELECT id, palabra_frase, traduccion, pronunciacion, "
                f"NULL AS significado FROM {tabla_sql} ORDER BY id"
            )

        for fila in cursor.fetchall():
            registros.append({
                "id": fila[0],
                "quechua": fila[1],
                "espanol": fila[2],
                "significado": fila[4],
                "pronunciacion": fila[3],
                "nivel": nivel,
                "categoria": categoria,
                "tabla_origen": nombre_tabla,
            })

    return registros


def buscar_vocabulario(texto, idioma_entrada, conexion_db):
    """Busca vocabulario local y conserva todos los resultados relevantes."""
    respuesta_vacia = {
        "encontrado": False,
        "ambiguo": False,
        "resultados": [],
        "fuente": "local",
    }

    if conexion_db is None or idioma_entrada not in _IDIOMAS_ENTRADA:
        return respuesta_vacia

    texto_comparacion = _normalizar_para_comparar(texto)
    if not texto_comparacion:
        return respuesta_vacia

    registros = _leer_registros_vocabulario(conexion_db)
    columna_busqueda = "espanol" if idioma_entrada == "espanol" else "quechua"

    exactos = [
        registro for registro in registros
        if _normalizar_para_comparar(registro[columna_busqueda]) == texto_comparacion
    ]

    candidatos = exactos
    if not candidatos:
        candidatos = [
            registro for registro in registros
            if texto_comparacion in _normalizar_para_comparar(
                registro[columna_busqueda]
            )
        ]

    if not candidatos:
        return respuesta_vacia

    return {
        "encontrado": True,
        "ambiguo": len(candidatos) > 1,
        "resultados": candidatos,
        "fuente": "local",
    }


def buscar_traduccion_local(texto, conexion_db):
    resultado = buscar_vocabulario(texto, "espanol", conexion_db)
    if not resultado["resultados"]:
        return None, None

    registro = resultado["resultados"][0]
    return registro["quechua"], registro["significado"]


def consultar_diccionario_local(palabra, conexion_db):
    resultado = buscar_vocabulario(palabra, "espanol", conexion_db)
    if not resultado["resultados"]:
        return None

    return resultado["resultados"][0]["quechua"]


def traducir_online(texto, groq_client):
    if not groq_client:
        print("[ALERTA GROQ]: no hay cliente disponible para fallback online.")
        return None

    texto = str(texto or "").strip()

    if texto == "":
        return None

    instruccion = (
        "Traduce del español al quechua. "
        "Devuelve únicamente la traducción en quechua, sin explicaciones, "
        "sin comillas, sin etiquetas, sin Markdown y sin texto adicional. "
        "Si no puedes determinar una traducción razonable, responde exactamente NO_ENCONTRADO."
    )

    try:
        print("[TRADUCTOR] FALLBACK ONLINE: consultando Groq...")
        respuesta = groq_client.chat.completions.create(
            model=os.environ.get(
                "YURA_GROQ_MODEL",
                "openai/gpt-oss-20b"
            ),
            messages=[
                {"role": "system", "content": instruccion},
                {"role": "user", "content": texto}
            ],
            temperature=0.1,
            max_tokens=80
        )

        contenido = respuesta.choices[0].message.content
        contenido = str(contenido or "").strip()
        print(f"[TRADUCTOR] GROQ RESPUESTA: {contenido}")

        contenido = re.sub(r"\s+", " ", contenido).strip()
        contenido = contenido.strip(" \t\n\r\"'`.,;:!?¿¡()[]{}")
        contenido = contenido.replace("Traducción:", "")
        contenido = contenido.replace("Quechua:", "")
        contenido = re.sub(r"^(?:traduccion|quechua)\s*:\s*", "", contenido, flags=re.IGNORECASE)
        contenido = contenido.strip()

        if contenido.upper() == "NO_ENCONTRADO":
            print("[TRADUCTOR] ONLINE: no encontrado")
            return None

        if contenido == "":
            print("[TRADUCTOR] ONLINE: vacía")
            return None

        print(f"[TRADUCTOR] ONLINE: {contenido}")
        return contenido

    except Exception as exc:
        print(f"[ERROR GROQ]: Fallback online falló: {exc}")
        return None


def ejecutar_traducir(
    escuchar_voz,
    hablar,
    conexion_db,
    groq_client,
    modo_activo,
    on_status=None,
):
    if on_status is None:
        on_status = lambda *args, **kwargs: None

    if conexion_db is None:
        hablar(
            "No puedo acceder al diccionario local ahora."
        )
        return "menu"

    while modo_activo():
        entrada = escuchar_voz()

        if entrada == "":
            hablar(
                "Necesito que repitas la palabra o frase."
            )
            continue

        entrada_norm = _normalizar_texto(entrada)

        if entrada_norm == "":
            hablar(
                "Necesito que repitas la palabra o frase."
            )
            continue

        if any(
            palabra in entrada_norm for palabra in (
                "salir",
                "apagar",
                "terminar",
                "adios",
                "volver",
                "menu",
                "regresar",
                "salir de yura"
            )
        ):
            hablar(
                "Regresando al menú principal."
            )
            return "menu"

        print(f"[TRADUCTOR] Usuario: {entrada_norm}")
        print("[TRADUCTOR] Buscando en BD local...")

        traduccion, significado = buscar_traduccion_local(
            entrada_norm,
            conexion_db
        )

        if traduccion:
            print(f"[TRADUCTOR] BD LOCAL: encontrada -> {traduccion}")
            on_status("PENSANDO", content=traduccion, translation=traduccion)
            respuesta = f"En quechua se dice: {traduccion}."
            if significado and str(significado).strip():
                respuesta += f" {str(significado).strip()}."
            hablar(respuesta)
            continue

        print(f"[TRADUCTOR] BD LOCAL: no encontrada -> {entrada_norm}")
        print("[TRADUCTOR] FALLBACK ONLINE: consultando Groq...")

        traduccion_online = traducir_online(
            entrada,
            groq_client
        )

        if traduccion_online:
            print(f"[TRADUCTOR] ONLINE: {traduccion_online}")
            on_status("PENSANDO", content=traduccion_online, translation=traduccion_online)
            hablar(
                f"En quechua se puede decir: {traduccion_online}."
            )
            continue

        print("[TRADUCTOR] ONLINE: error -> no se obtuvo respuesta del servicio")
        hablar(
            "No estoy seguro de cómo traducir esa frase. "
            "¿Puedes decirla de otra manera?"
        )

    return "continuar"
