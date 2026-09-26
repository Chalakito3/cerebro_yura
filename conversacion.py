import os
import random
import re
import sqlite3
from difflib import SequenceMatcher

import traductor


PRESENTACION_YURA = (
    "Ñuqaqa Yura kani. Robotmi kani, qhichwa simita rimanakuypaq yanapakuq. "
    "Qhichwa simita rimanakuyta, rimaykunata kallpachayta yanapani. "
    "Imapin yanapaykiman?"
)


FRASES_QUECHUA_CONOCIDAS = {
    "hola": "Rimaykullayki",
    "rimaykullayki": "Rimaykullayki",
    "rima el cowley que": "Rimaykullayki",
    "imaynalla kachkanki": "Imaynalla kachkanki",
    "y minaya cachan que": "Imaynalla kachkanki",
    "anchata munakuyki": "Anchata munakuyki",
    "anchata munacuyki": "Anchata munakuyki",
    "anchata kuyayki": "Anchata kuyayki",
    "allin p'unchay": "Allin p'unchay",
    "allin punchay": "Allin p'unchay",
    "yusulpayki": "Yusulpayki",
    "gracias": "Yusulpayki",
    "ari": "Ari",
    "si": "Ari",
    "sí": "Ari",
    "mana": "Mana",
    "no": "Mana",
    "sulpayki": "Sulpayki",
    "imataq sutiyki": "Imataq sutiyki",
    "sutiymi": "Sutiymi",
    "maymanta kanki": "Maymanta kanki",
    "allinmi": "Allinmi",
    "qamri": "Qamrí",
    "kayqa": "Kayqa",
    "quechua": "Quechua",
    "hablar en quechua": "Hablar en quechua",
    "ensename quechua": "Enséñame quechua",
    "quiero aprender quechua": "Quiero aprender quechua"
}


_conexion_vocabulario = None
_sesion_educativa = None


def cancelar_sesion_educativa():
    """Cancela una práctica pendiente al cambiar a otro modo."""
    global _sesion_educativa
    _sesion_educativa = None


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
        .replace("ñ", "n")
    )
    texto = re.sub(r"[^a-z0-9\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


def _coincide_clave_intencion(texto, claves, similitud_minima=0.82):
    tokens = _normalizar_texto(texto).split()
    texto_compacto = "".join(tokens)

    for clave in claves:
        if clave in texto_compacto:
            return True

        cantidad_tokens = len(clave.split())
        for inicio in range(len(tokens)):
            for final in range(
                inicio + 1,
                min(len(tokens), inicio + cantidad_tokens + 2) + 1
            ):
                ventana = "".join(tokens[inicio:final])
                if SequenceMatcher(None, ventana, clave).ratio() >= similitud_minima:
                    return True

    return False


def _detectar_intencion(texto):
    texto_normalizado = _normalizar_texto(texto)

    if any(palabra in texto_normalizado for palabra in (
        "salir", "terminar", "adios", "hasta luego", "tupananchiskama",
        "nos vemos", "me voy", "menu"
    )):
        return "salir"

    if any(frase in texto_normalizado for frase in (
        "otra vez", "repite", "repetir", "siguiente"
    )):
        return "repetir"

    if (
        _coincide_clave_intencion(
            texto_normalizado,
            ("ensename", "ensenar")
        )
        or _coincide_clave_intencion(texto_normalizado, ("aprender",))
        or (
            _coincide_clave_intencion(texto_normalizado, ("muestrame", "mostrar"))
            and _coincide_clave_intencion(texto_normalizado, ("palabra", "quechua"))
        )
    ):
        return "aprender"

    if (
        _coincide_clave_intencion(texto_normalizado, ("practicar", "practica"))
        or _coincide_clave_intencion(texto_normalizado, ("preguntame",))
        or _coincide_clave_intencion(
            texto_normalizado,
            ("ejercicio", "prueba", "jugar")
        )
    ):
        return "practicar"

    if any(frase in texto_normalizado for frase in (
        "como se dice", "como digo", "como puedo decir", "traduce",
        "traducir", "traduccion"
    )):
        return "traducir"

    if any(frase in texto_normalizado for frase in (
        "que significa", "significado", "explicame"
    )):
        return "significado"

    if any(frase in texto_normalizado for frase in (
        "hablar en quechua", "habla en quechua", "conversar en quechua",
        "conversemos en quechua"
    )):
        return "conversar_quechua"

    return "conversar"


def _obtener_conexion_vocabulario():
    global _conexion_vocabulario

    if _conexion_vocabulario is not None:
        return _conexion_vocabulario

    ruta_db = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "diccionario.db"
    )

    try:
        _conexion_vocabulario = sqlite3.connect(ruta_db)
    except sqlite3.Error as exc:
        print(f"[CONVERSACION] No se pudo abrir el vocabulario: {exc}")
        return None

    return _conexion_vocabulario


def _obtener_vocabulario_para_practica(conexion_db):
    """Obtiene registros locales sin duplicar vocabulario en este módulo."""
    candidatos = {}

    for letra in ("a", "e", "i", "o", "u"):
        resultado = traductor.buscar_vocabulario(
            letra,
            "espanol",
            conexion_db
        )

        for registro in resultado["resultados"]:
            clave = (registro["tabla_origen"], registro["id"])
            candidatos[clave] = registro

    return list(candidatos.values())


def _seleccionar_leccion():
    conexion_db = _obtener_conexion_vocabulario()
    if conexion_db is None:
        return None

    candidatos = _obtener_vocabulario_para_practica(conexion_db)
    if not candidatos:
        return None

    return random.choice(candidatos)


def _comenzar_practica():
    global _sesion_educativa

    registro = _seleccionar_leccion()
    if registro is None:
        return (
            "No pude cargar una palabra del vocabulario local. "
            "Probemos más tarde."
        )

    _sesion_educativa = {
        "registro": registro,
        "estado": "esperando_repeticion",
    }

    significado = registro["significado"] or "una palabra de uso cotidiano"
    return (
        f"Practiquemos una palabra. En quechua se dice "
        f"{registro['quechua']}. Significa {registro['espanol']}: "
        f"{significado}. Repítela, por favor."
    )


def _evaluar_respuesta(respuesta_usuario, respuesta_correcta):
    usuario = _normalizar_texto(respuesta_usuario)
    correcta = _normalizar_texto(respuesta_correcta)

    if not usuario or not correcta:
        return False

    if usuario == correcta:
        return True

    usuario_compacto = (
        re.sub(r"\s+", "", usuario)
        .replace("q", "k")
        .replace("v", "b")
        .replace("h", "")
        .replace("ll", "y")
    )
    correcta_compacta = (
        re.sub(r"\s+", "", correcta)
        .replace("q", "k")
        .replace("v", "b")
        .replace("h", "")
        .replace("ll", "y")
    )

    if usuario_compacto == correcta_compacta:
        return True

    similitud_compacta = SequenceMatcher(
        None,
        usuario_compacto,
        correcta_compacta
    ).ratio()
    similitud_cruda = SequenceMatcher(
        None,
        usuario,
        correcta
    ).ratio()

    return (
        similitud_compacta >= 0.75
        or (
            similitud_cruda >= 0.75
            and (usuario in correcta or correcta in usuario)
        )
    )


def _continuar_practica():
    global _sesion_educativa

    registro = _seleccionar_leccion()
    if registro is None:
        _sesion_educativa = None
        return "No pude cargar otra palabra del vocabulario local."

    _sesion_educativa = {
        "registro": registro,
        "estado": "esperando_repeticion",
    }
    significado = registro["significado"] or "una palabra de uso cotidiano"
    return (
        f"Otra palabra: {registro['quechua']} significa "
        f"{registro['espanol']}, {significado}. Repítela, por favor."
    )


def _procesar_sesion_educativa(entrada):
    global _sesion_educativa

    if _sesion_educativa is None:
        return None

    intencion = _detectar_intencion(entrada)
    if intencion == "salir":
        _sesion_educativa = None
        return {
            "accion": "menu",
                "respuesta": "Terminamos por ahora. Tupananchiskama."
        }

    if intencion == "repetir":
        return {
            "accion": "responder",
            "respuesta": _continuar_practica()
        }

    registro = _sesion_educativa["registro"]
    es_correcta = _evaluar_respuesta(
        entrada,
        registro["quechua"]
    )
    _sesion_educativa["estado"] = "resultado"

    if es_correcta:
        respuesta = (
            f"Muy bien. Dijiste {registro['quechua']} correctamente. "
            "Di otra vez o continuar para practicar otra palabra, "
            "o salir para terminar."
        )
    else:
        respuesta = (
            f"Todavía no. La forma correcta es {registro['quechua']}. "
            "Repítela y luego di otra vez para continuar, o salir para terminar."
        )

    return {
        "accion": "responder",
        "respuesta": respuesta
    }


def _extraer_termino(entrada):
    texto = _normalizar_texto(entrada)
    for marcador in (
        "como puedo decir",
        "como se dice",
        "como digo",
        "traduce",
        "que significa",
        "significado de",
        "explicame"
    ):
        if marcador in texto:
            termino = texto.split(marcador, 1)[1].strip()
            termino = re.sub(r"\s+(?:en|de)\s+quechua$", "", termino)
            termino = re.sub(r"^(?:el|la|un|una)\s+", "", termino)
            termino = re.sub(r"^(?:color|colores)\s+", "", termino)
            return termino.strip()
    texto = re.sub(r"\s+(?:en|de)\s+quechua$", "", texto)
    texto = re.sub(r"^(?:el|la|un|una)\s+", "", texto)
    texto = re.sub(r"^(?:color|colores)\s+", "", texto)
    return texto.strip()


def _responder_consulta_local(entrada, idioma_entrada):
    conexion_db = _obtener_conexion_vocabulario()
    if conexion_db is None:
        return None

    termino = _extraer_termino(entrada)
    resultado = traductor.buscar_vocabulario(
        termino,
        idioma_entrada,
        conexion_db
    )

    if not resultado["encontrado"]:
        return None

    if resultado["ambiguo"]:
        opciones = "; ".join(
            f"{registro['espanol']} ({registro['categoria']})"
            for registro in resultado["resultados"]
        )
        return f"Encontré varios significados: {opciones}."

    registro = resultado["resultados"][0]
    if idioma_entrada == "espanol":
        termino = registro["espanol"].lower()
        quechua = registro["quechua"]
        categoria = _normalizar_texto(registro["categoria"])
        if categoria == "colores":
            return (
                f"En quechua, {termino} se dice {quechua}. Por ejemplo, "
                f"si señalas algo de ese color puedes decir «{quechua}»; "
                f"esa palabra significa {termino}."
            )
        if categoria == "saludos":
            return (
                f"Para decir {termino} en quechua, usa «{quechua}». "
                f"Puedes saludar así cuando llegue ese momento del día; "
                f"por ejemplo: «{quechua}» al encontrarte con alguien."
            )
        return (
            f"En quechua se dice {quechua}, que significa {termino}. "
            f"Puedes practicarla usándola para describir algo de tu día."
        )

    significado = registro["significado"]
    respuesta = f"{registro['quechua']} significa {registro['espanol']}."
    if significado:
        respuesta += f" {significado}."
    return respuesta


def _responder_traduccion_desconocida(entrada):
    texto = _normalizar_texto(entrada)
    if "naranja" in texto or "color naranja" in texto:
        return (
            "Todavía no tengo el color naranja en mi diccionario local, "
            "pero puedes practicar con otros colores básicos como rojo, azul o verde."
        )

    termino = _extraer_termino(entrada).strip()
    if not termino:
        return None

    if any(palabra in texto for palabra in (
        "como se dice", "como digo", "como puedo decir", "traduce", "traducir"
    )):
        return (
            f"No tengo una traducción segura de '{termino}' en mi vocabulario local todavía. "
            "Puedo ayudarte con otra palabra o frase en quechua."
        )

    return None


def interpretar_entrada_quechua(texto):
    """Corrige sólo frases quechuas conocidas o aproximaciones claras."""
    texto_normalizado = _normalizar_texto(texto)

    if texto_normalizado == "":
        return ""

    for variante, frase_correcta in FRASES_QUECHUA_CONOCIDAS.items():
        if _normalizar_texto(variante) == texto_normalizado:
            return frase_correcta

    mejor_coincidencia = None
    mejor_similitud = 0.0

    for variante, frase_correcta in FRASES_QUECHUA_CONOCIDAS.items():
        if len(texto_normalizado.split()) < 2:
            continue

        similitud = SequenceMatcher(
            None,
            texto_normalizado,
            _normalizar_texto(variante)
        ).ratio()

        if similitud > mejor_similitud:
            mejor_similitud = similitud
            mejor_coincidencia = frase_correcta

    if mejor_similitud >= 0.82:
        return mejor_coincidencia

    return texto


def _es_tema_quechua(texto):
    """Limita la conversación al aprendizaje y uso del quechua."""
    texto_normalizado = _normalizar_texto(texto)
    tokens = set(texto_normalizado.split())
    if tokens.intersection({"ingles", "english"}):
        return False

    temas_permitidos = {
        "quechua", "qhichwa", "palabra", "palabras", "frase", "frases",
        "idioma", "significa", "escribe", "escribir", "saludo", "saludos",
        "vocabulario", "aprender", "practicar", "conversar", "hablar",
        "nombre", "hola", "gracias", "adios", "bien", "mal", "cultura",
        "ayuda", "ari", "mana"
    }
    if any(
        token in temas_permitidos or token.startswith(("traduc", "pronunci"))
        for token in tokens
    ):
        return True
    return any(
        f" {_normalizar_texto(frase)} " in f" {texto_normalizado} "
        for frase in FRASES_QUECHUA_CONOCIDAS
    )


def _responder_frase_local(texto):
    texto_normalizado = _normalizar_texto(texto)
    respuestas = {
        "si": "Sí, entendido. ¿Qué palabra en quechua practicamos?",
        "no": "Está bien. Cuando quieras, seguimos practicando quechua.",
        "ari": "Ari, entendido.",
        "mana": "Mana, entendido.",
        "hola": "Rimaykullayki significa hola.",
        "yusulpayki imaynalla kachkanki": (
            "Yusulpayki significa gracias. Imaynalla kachkanki significa "
            "¿cómo estás?"
        ),
        "anchata munakuyki": (
            "Anchata munakuyki significa te quiero mucho. "
            "Es una expresión afectuosa en quechua."
        ),
        "anchata kuyayki": (
            "Anchata kuyayki significa te quiero mucho."
        ),
        "rimaykullayki": "Rimaykullayki significa hola. Es un saludo en quechua.",
        "yusulpayki": "Yusulpayki significa gracias.",
        "gracias": "Yusulpayki significa gracias.",
    }

    if texto_normalizado in {"buenas tardes", "buenas noches"}:
        return _responder_consulta_local(texto_normalizado, "espanol")
    if texto_normalizado in {"allin sukay", "allin tuta"}:
        return _responder_consulta_local(texto_normalizado, "quechua")

    for frase, respuesta in respuestas.items():
        frase_normalizada = _normalizar_texto(frase)
        if (
            texto_normalizado == frase_normalizada
            or (
                len(frase_normalizada.split()) > 1
                and f" {frase_normalizada} " in f" {texto_normalizado} "
            )
        ):
            return respuesta
    return None


def _corregir_repeticion_quechua(texto):
    """Reduce repeticiones del reconocimiento y conserva frases conocidas."""
    tokens = _normalizar_texto(texto).split()
    reducidos = []
    for token in tokens:
        if not reducidos or token != reducidos[-1]:
            reducidos.append(token)

    compacto = " ".join(reducidos)
    for frase in (
        "yusulpayki imaynalla kachkanki",
        "rimaykullayki",
        "anchata munakuyki",
        "imaynalla kachkanki",
    ):
        if frase in compacto:
            return frase
    return compacto


def _consultar_groq(entrada, groq_client, historial=None):
    if not groq_client:
        print(
            "[CONVERSACION] Error Groq: "
            "el cliente no está disponible."
        )
        return None

    prompt_sistema = (
        "Eres Yura, un asistente educativo amable para estudiantes de sexto "
        "de primaria. Conversa naturalmente en espanol o quechua boliviano, "
        "usando el mismo idioma que el estudiante. Puedes mezclar ambos si "
        "el estudiante lo hace. Responde en una sola frase o como máximo "
        "dos frases cortas, claras, calidas y aptas para ser leidas en voz "
        "alta. No uses Markdown, listas ni explicaciones largas. "
        "Ayuda a practicar quechua sin convertir cada respuesta en una clase. "
        "No inventes traducciones ni afirmes datos dudosos; pide aclaracion "
        "cuando no entiendas."
    )

    mensajes = [{"role": "system", "content": prompt_sistema}]
    if historial:
        mensajes.extend(historial[-8:])
    mensajes.append({"role": "user", "content": entrada})

    try:
        print("[CONVERSACION] Consultando Groq...")
        respuesta = groq_client.chat.completions.create(
            model=os.environ.get(
                "YURA_GROQ_MODEL",
                "openai/gpt-oss-20b"
            ),
            messages=mensajes,
            temperature=0.7,
            max_tokens=300
        )

        print("[DEBUG GROQ] respuesta:", respuesta)
        print("[DEBUG GROQ] choices:", respuesta.choices)

        if respuesta.choices:
            msg = respuesta.choices[0].message
            print("[DEBUG GROQ] message:", msg)
            print("[DEBUG GROQ] content:", repr(getattr(msg, "content", None)))
            print(
                "[DEBUG GROQ] reasoning_content:",
                repr(getattr(msg, "reasoning_content", None))
            )

        contenido = str(
            respuesta.choices[0].message.content or ""
        ).strip()

        if not contenido:
            print(
                "[CONVERSACION] Error Groq: "
                "la respuesta llegó vacía."
            )
            return None

        if historial is not None:
            historial.append({"role": "user", "content": entrada})
            historial.append({"role": "assistant", "content": contenido})

        print(f"[CONVERSACION] Groq respondió: {contenido}")
        return contenido

    except Exception as exc:
        print(f"[CONVERSACION] Error Groq: {exc}")
        return None


def procesar_entrada(entrada, groq_client, historial=None):
    entrada_original = str(entrada or "").strip()
    entrada_original = _corregir_repeticion_quechua(entrada_original)
    entrada = _normalizar_texto(entrada_original)

    if entrada == "":
        return {
            "accion": "responder",
            "respuesta": "No logré escucharte."
        }

    respuesta_local = _responder_frase_local(entrada_original)
    if respuesta_local:
        return {
            "accion": "responder",
            "respuesta": respuesta_local
        }

    resultado_sesion = _procesar_sesion_educativa(entrada_original)
    if resultado_sesion is not None:
        return resultado_sesion

    intencion = _detectar_intencion(entrada)

    if intencion == "salir":
        return {
            "accion": "menu",
            "respuesta": "Hasta luego. Tupananchiskama."
        }

    if intencion in {"aprender", "practicar"}:
        return {
            "accion": "responder",
            "respuesta": _comenzar_practica()
        }

    entrada_comando = re.sub(
        r"^(?:yura|yo era|oye yura)\s+",
        "",
        entrada
    ).strip()

    if (
        "presentate" in entrada_comando
        or "presentarte" in entrada_comando
        or "quien eres" in entrada_comando
        or "puedes hablar en quechua" in entrada_comando
        or "puedes hablar en que" in entrada_comando
    ):
        return {
            "accion": "responder",
            "respuesta": PRESENTACION_YURA
        }

    if intencion == "traducir":
        respuesta_local = _responder_consulta_local(
            entrada_original,
            "espanol"
        )
        if respuesta_local:
            return {
                "accion": "responder",
                "respuesta": respuesta_local
            }

        respuesta_local = _responder_traduccion_desconocida(entrada_original)
        if respuesta_local:
            return {
                "accion": "responder",
                "respuesta": respuesta_local
            }

        if not groq_client:
            return {
                "accion": "responder",
                "respuesta": (
                    "No tengo la traducción exacta en mi diccionario local y "
                    "ahora mismo no está disponible la ayuda online. Prueba otra palabra o frase en quechua."
                )
            }

    if intencion == "significado":
        respuesta_local = _responder_consulta_local(
            entrada_original,
            "quechua"
        )
        if respuesta_local:
            return {
                "accion": "responder",
                "respuesta": respuesta_local
            }

    if not _es_tema_quechua(entrada_original):
        return {
            "accion": "responder",
            "respuesta": (
                "Soy Yura, un robot educativo que ayuda a practicar quechua. "
                "Puedo enseñarte vocabulario, traducciones y saludos; no vendo "
                "autos ni converso en inglés."
            )
        }

    respuesta_local = _responder_frase_local(entrada_original)
    if respuesta_local:
        return {
            "accion": "responder",
            "respuesta": respuesta_local
        }

    entrada_para_groq = entrada_original
    if intencion == "conversar_quechua":
        entrada_para_groq = (
            f"Responde en quechua boliviano de forma breve: {entrada_original}"
        )

    entrada_para_groq = interpretar_entrada_quechua(entrada_para_groq)
    print(f"[CONVERSACION] Usuario: {entrada_para_groq}")
    respuesta = _consultar_groq(
        entrada_para_groq,
        groq_client,
        historial
    )

    if respuesta is None:
        respuesta = (
            "No alcancé a entender esa frase. Intenta decirla un poco más "
            "despacio o prueba: «¿cómo digo amarillo en quechua?»"
        )

    return {
        "accion": "responder",
        "respuesta": respuesta
    }