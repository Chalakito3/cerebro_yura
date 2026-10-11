#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import unicodedata
import depuracion

import texto as texto_util


_IDIOMAS_ENTRADA = {"espanol", "quechua"}
_TABLA_VOCABULARIO = re.compile(r"^nivel(?P<nivel>\d+)_(?P<categoria>[a-z0-9_]+)$")


def _identificador_sql(nombre):
    """Cita un identificador obtenido del esquema SQLite, no del usuario."""
    return '"' + str(nombre).replace('"', '""') + '"'


def _normalizar_texto(texto):
    # Conserva ñ y apóstrofo: antes "niño" pasaba a "ni o" y no se traducía.
    return texto_util.normalizar(texto)


def extraer_termino(entrada):
    """Quita "cómo se dice", artículos y "en quechua" para buscar solo la
    palabra: "¿cómo se dice el perro en quechua?" -> "perro"."""
    texto = _normalizar_texto(entrada)
    for marcador in (
        "como puedo decir",
        "como se dice",
        "como se escribe",
        "como se pronuncia",
        "como digo",
        "que quiere decir",
        "que significa",
        "significado de",
        "traduceme",
        "traduce",
        "explicame",
    ):
        coincidencia = re.search(
            r"(?<![a-zñ'])" + re.escape(marcador) + r"(?![a-zñ'])",
            texto
        )
        if coincidencia:
            texto = texto[coincidencia.end():].strip()
            # El reconocedor a veces repite la pregunta: "cómo se dice, cómo
            # se dice cómo estás" (29/09/2026).
            while texto.startswith(marcador + " "):
                texto = texto[len(marcador):].strip()
            break
    # Hasta el primer "en quechua": el reconocedor a veces repite la frase
    # ("verde en quechua verde en quechua").
    texto = re.sub(r"\s+(?:en|de|al)\s+(?:quechua|qhichwa|español|espanol)\b.*$", "", texto)
    # El reconocedor a veces corta "quechua": "perro en que", "en quechu".
    texto = re.sub(r"\s+en\s+(?:que|quech\w*|qhich\w*|kech\w*)$", "", texto)
    # "verde quechua", "perro en" (sin la palabra completa).
    texto = re.sub(r"\s+(?:quechua|qhichwa|en)$", "", texto)
    texto = re.sub(r"^(?:la palabra|el|la|los|las|un|una)\s+", "", texto)
    texto = re.sub(r"^(?:color|colores)\s+", "", texto)
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
        patron = re.compile(
            r"(?<![a-zñ'])" + re.escape(texto_comparacion) + r"(?![a-zñ'])"
        )
        candidatos = [
            registro for registro in registros
            if patron.search(_normalizar_para_comparar(registro[columna_busqueda]))
        ]

    if not candidatos and idioma_entrada == "quechua":
        candidatos = _buscar_quechua_aproximado(texto, registros)
    if not candidatos and idioma_entrada == "espanol":
        candidatos = _buscar_espanol_aproximado(texto_comparacion, registros)

    if not candidatos:
        return respuesta_vacia

    return {
        "encontrado": True,
        "ambiguo": len(candidatos) > 1,
        "resultados": candidatos,
        "fuente": "local",
    }


def _buscar_espanol_aproximado(buscado, registros):
    """El reconocedor a veces cambia una letra ("verdi" por verde). Si la
    palabra es larga y solo UNA palabra del diccionario está a una letra de
    distancia, se usa esa."""
    if len(buscado) < 5 or " " in buscado:
        return []
    cercanas = {}
    for registro in registros:
        espanol = _normalizar_para_comparar(registro["espanol"])
        if espanol and texto_util.distancia_edicion(buscado, espanol) == 1:
            cercanas.setdefault(espanol, []).append(registro)
    if len(cercanas) == 1:
        return next(iter(cercanas.values()))
    return _buscar_familia_espanol(buscado, registros)


# Terminaciones de la misma familia de palabras: plata -> plat-eado,
# casa -> cas-ita, perro -> perr-ito (pedido en vivo: "¿cómo se dice plata?").
_TERMINACIONES_FAMILIA = ("eado", "eada", "ado", "ada", "ito", "ita", "itos", "itas", "illo", "illa", "s", "es")


def _buscar_familia_espanol(buscado, registros):
    if len(buscado) < 4 or " " in buscado:
        return []
    raiz = buscado[:-1] if buscado[-1] in "aeo" else buscado
    familia = {}
    for registro in registros:
        espanol = _normalizar_para_comparar(registro["espanol"])
        if not espanol or " " in espanol or espanol == buscado:
            continue
        resto = espanol[len(raiz):] if espanol.startswith(raiz) else None
        if resto in _TERMINACIONES_FAMILIA or (
            buscado.startswith(espanol[:-1]) and buscado[len(espanol[:-1]):] in _TERMINACIONES_FAMILIA
        ):
            familia.setdefault(espanol, []).append(registro)
    return next(iter(familia.values())) if len(familia) == 1 else []


def _buscar_quechua_aproximado(texto, registros):
    """El reconocedor de voz no escribe apóstrofos ni distingue q/k: "qumir"
    o "kumir" por Q'umir. Se compara la forma simplificada (la misma del
    evaluador) y, si no basta, lo aprendido de los audios de la docente."""
    buscado = texto_util.simplificar_quechua(texto)
    if len(buscado.replace(" ", "")) < 3:
        return []
    junto = buscado.replace(" ", "")
    candidatos = [
        registro for registro in registros
        if registro["quechua"] and any(
            texto_util.simplificar_quechua(registro["quechua"], ll).replace(" ", "") == junto
            for ll in ("l", "y")
        )
    ]
    if candidatos:
        return candidatos
    import pronunciaciones
    palabra = pronunciaciones.palabra_por_variante(texto)
    if palabra is None:
        return []
    return [
        registro for registro in registros
        if _normalizar_para_comparar(registro["quechua"]) == _normalizar_para_comparar(palabra)
    ]


# Palabras que no aparecen en ninguna fuente boliviana (documento 002,
# sección 14.4). El equipo decidió dejarlas en el diccionario, pero el juego
# no las pregunta.
PALABRAS_SIN_VERIFICAR = {
    "iglesia", "jarra", "cuchara", "cuchillo", "sarten", "tijera",
    "espalda baja", "dedos del pie", "cuaderno", "mochila", "chicha dulce",
    "olla pequeña", "rosado", "sendero",
}

CATEGORIAS_DEL_JUEGO = {
    "animales", "familia", "colores", "partes_del_cuerpo", "elementos_naturales",
    "alimentos", "elementos_casa", "objetos_escolares", "numeros",
}


def palabras_para_juego(conexion_db):
    """Palabras en castellano que el juego puede preguntar.

    Solo vocabulario básico, verificado y con una única traducción (se
    excluyen las ambiguas como papa/papá y las que se escriben igual en los
    dos idiomas, porque no enseñan nada).
    """
    if conexion_db is None:
        return []
    try:
        registros = _leer_registros_vocabulario(conexion_db)
    except Exception as exc:
        print(f"[JUEGO] No se pudo leer el vocabulario: {exc}")
        return []

    palabras = set()
    for registro in registros:
        espanol = str(registro["espanol"] or "").strip()
        quechua = str(registro["quechua"] or "").strip()
        if registro["categoria"] not in CATEGORIAS_DEL_JUEGO or not espanol or not quechua:
            continue
        if registro["categoria"] == "numeros" and registro["id"] > 10:
            continue
        if any(signo in espanol for signo in "/()") or len(espanol.split()) > 2:
            continue
        if _normalizar_para_comparar(espanol) in PALABRAS_SIN_VERIFICAR:
            continue
        if _normalizar_para_comparar(espanol) == _normalizar_para_comparar(quechua):
            continue
        if len(buscar_vocabulario(espanol, "espanol", conexion_db)["resultados"]) != 1:
            continue
        palabras.add(espanol.lower())
    return sorted(palabras)


def consultar_diccionario_local(palabra, conexion_db):
    resultado = buscar_vocabulario(palabra, "espanol", conexion_db)
    if not resultado["resultados"]:
        return None

    return resultado["resultados"][0]["quechua"]


_PALABRAS_VACIAS = {
    "como", "dice", "decir", "digo", "quechua", "que", "para", "con", "una",
    "uno", "unos", "unas", "los", "las", "del", "por", "hola", "yura", "dime",
    "quiero", "aprender", "palabra", "palabras", "sobre", "cual", "cuales",
    "significa", "traduce", "traducir", "puedo", "puedes", "esta", "este",
    "eso", "esa", "muy", "mas", "tengo", "ensename", "sabes", "algo", "mi",
    "tu", "hablar", "habla", "idioma", "frase", "frases", "cosas", "oye",
}


def _coincide_palabra(token, palabra):
    if token == palabra:
        return True
    return (
        len(token) >= 4
        and len(palabra) >= 4
        and (token.startswith(palabra) or palabra.startswith(token))
    )


# Base para conversar que Groq recibe siempre (además de lo relacionado con
# lo que se dijo): así arma sus frases con el diccionario y no inventa.
_CATEGORIAS_BASE = {"saludos", "dialogo_infantil", "pronombres", "preguntas"}


def vocabulario_relevante(texto, conexion_db, limite=90):
    """Elige del diccionario las palabras relacionadas con lo que se preguntó.

    Siempre incluye los saludos y agrega las palabras mencionadas y las de
    cualquier tema nombrado (por ejemplo "familia" o "colores").
    """
    if conexion_db is None:
        return []

    try:
        registros = _leer_registros_vocabulario(conexion_db)
    except Exception as exc:
        print(f"[TRADUCTOR] No se pudo leer el vocabulario: {exc}")
        return []

    tokens = {
        token
        for token in re.findall(r"[a-zñ']+", _normalizar_para_comparar(texto))
        if len(token) >= 3 and token not in _PALABRAS_VACIAS
    }

    elegidos = []
    for registro in registros:
        palabras_categoria = registro["categoria"].split("_")
        palabras_registro = re.findall(
            r"[a-zñ']+",
            _normalizar_para_comparar(
                f"{registro['espanol']} {registro['quechua']}"
            )
        )
        if (
            registro["categoria"] in _CATEGORIAS_BASE
            or any(
                _coincide_palabra(token, palabra)
                for token in tokens
                for palabra in palabras_registro + palabras_categoria
            )
        ):
            elegidos.append(registro)

    return elegidos[:limite]


def describir_opciones(registros, limite=3):
    """Describe en voz alta las traducciones cuando una palabra es ambigua."""
    opciones = "; ".join(
        f"{registro['espanol']}, de {registro['categoria'].replace('_', ' ')}, "
        f"se dice {registro['quechua']}"
        for registro in registros[:limite]
    )
    return f"Tiene varios significados: {opciones}."


def formatear_vocabulario(registros):
    return "\n".join(
        f"- {registro['espanol']} = {registro['quechua']}"
        for registro in registros
    )


def consultar_modelo_groq(groq_client, mensajes, temperatura, max_tokens):
    """Llama a Groq limitando el razonamiento interno del modelo.

    Los modelos gpt-oss "piensan" antes de responder y ese pensamiento
    consume el límite de tokens; sin reasoning_effort bajo, la respuesta
    visible puede llegar cortada o vacía.
    """
    modelo = os.environ.get("YURA_GROQ_MODEL", "openai/gpt-oss-120b")
    parametros = {
        "model": modelo,
        "messages": mensajes,
        "temperature": temperatura,
        "max_completion_tokens": max_tokens + 400,
    }
    if "gpt-oss" in modelo:
        parametros["reasoning_effort"] = "low"
    return groq_client.chat.completions.create(**parametros)


def traducir_online(texto, groq_client, conexion_db=None):
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

    vocabulario = vocabulario_relevante(texto, conexion_db)
    if vocabulario:
        instruccion += (
            "\n\nVocabulario verificado (español = quechua):\n"
            f"{formatear_vocabulario(vocabulario)}\n"
            "Usa estas palabras cuando correspondan. Si la traducción "
            "necesita una palabra quechua que no está en la lista y no "
            "estás completamente seguro de ella, responde exactamente "
            "NO_ENCONTRADO. Nunca inventes palabras en quechua."
        )

    try:
        print("[TRADUCTOR] FALLBACK ONLINE: consultando Groq...")
        respuesta = consultar_modelo_groq(
            groq_client,
            [
                {"role": "system", "content": instruccion},
                {"role": "user", "content": texto}
            ],
            temperatura=0.1,
            max_tokens=80
        )

        contenido = respuesta.choices[0].message.content
        # Nada en otro idioma ni sobre compras (29/09/2026).
        contenido = texto_util.limpiar_respuesta_ia(str(contenido or "").strip())
        print(f"[TRADUCTOR] GROQ RESPUESTA: {contenido}")

        contenido = re.sub(r"\s+", " ", contenido).strip()
        contenido = contenido.strip(" \t\n\r\"'`.,;:!?¿¡()[]{}")
        contenido = contenido.replace("Traducción:", "")
        contenido = contenido.replace("Quechua:", "")
        contenido = re.sub(r"^(?:traduccion|quechua)\s*:\s*", "", contenido, flags=re.IGNORECASE)
        contenido = contenido.strip()

        if re.sub(r"[\s_.]", "", contenido.upper()).startswith("NOENCONTRADO"):
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

    silencios_seguidos = 0

    while modo_activo():
        entrada = escuchar_voz()
        entrada_norm = _normalizar_texto(entrada)

        if entrada_norm == "":
            # Sin salida, el modo repetía "Necesito que repitas" para siempre.
            silencios_seguidos += 1
            if silencios_seguidos >= 3:
                hablar(
                    "No escucho a nadie. Regreso al menú principal."
                )
                return "menu"
            hablar(
                "Necesito que repitas la palabra o frase."
            )
            continue

        silencios_seguidos = 0

        # Solo la orden completa sale del traductor, así se pueden traducir
        # palabras como "adiós", "volver" o "apagar".
        if _ORDEN_SALIR_TRADUCTOR.fullmatch(entrada_norm):
            hablar(
                "Regresando al menú principal."
            )
            return "menu"

        termino = extraer_termino(entrada_norm) or entrada_norm

        depuracion.voz("[TRADUCTOR] Usuario", entrada_norm)
        print("[TRADUCTOR] Buscando en BD local...")

        resultado_local = buscar_vocabulario(termino, "espanol", conexion_db)

        # Sin tildes, "papá" y "papa" suenan igual: se dicen ambas opciones.
        if resultado_local["ambiguo"]:
            opciones = resultado_local["resultados"][:3]
            respuesta = describir_opciones(opciones)
            print(f"[TRADUCTOR] BD LOCAL: varias opciones -> {respuesta}")
            on_status(
                "PENSANDO",
                content=" / ".join(r["quechua"] for r in opciones),
                translation=" / ".join(r["espanol"] for r in opciones),
                fijar=True
            )
            hablar(respuesta)
            continue

        if resultado_local["encontrado"]:
            registro = resultado_local["resultados"][0]
            traduccion = registro["quechua"]
            significado = registro["significado"]
            print(f"[TRADUCTOR] BD LOCAL: encontrada -> {traduccion}")
            on_status(
                "PENSANDO",
                content=traduccion,
                translation=registro["espanol"],
                fijar=True
            )
            respuesta = f"En quechua se dice: {traduccion}."
            if significado and str(significado).strip():
                respuesta += f" {str(significado).strip()}."
            hablar(respuesta)
            continue

        depuracion.voz("[TRADUCTOR] BD LOCAL: no encontrada", termino)
        print("[TRADUCTOR] FALLBACK ONLINE: consultando Groq...")

        traduccion_online = traducir_online(
            termino,
            groq_client,
            conexion_db
        )

        if traduccion_online:
            print(f"[TRADUCTOR] ONLINE: {traduccion_online}")
            on_status(
                "PENSANDO",
                content=traduccion_online,
                translation=termino,
                fijar=True
            )
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


_ORDEN_SALIR_TRADUCTOR = re.compile(
    r"(?:yura )?(?:quiero )?(?:"
    r"salir(?: del traductor)?|terminar|menu(?: principal)?|"
    r"(?:volver|regresar|ir) al menu(?: principal)?|volver|regresar"
    r")(?: por favor)?"
)
