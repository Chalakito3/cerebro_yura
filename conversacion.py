import os
import random
import re
import sqlite3
from difflib import SequenceMatcher

import resultados
import depuracion
import pronunciaciones
import texto as texto_util
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
    "enséñame quechua": "Enséñame quechua",
    "quiero aprender quechua": "Quiero aprender quechua"
}


_conexion_vocabulario = None
_sesion_educativa = None


def cancelar_sesion_educativa():
    """Cancela una práctica pendiente al cambiar a otro modo."""
    global _sesion_educativa
    _sesion_educativa = None


def _normalizar_texto(texto):
    # Conserva ñ y apóstrofo: antes "ñawi" pasaba a "nawi" y "k'anchay" a
    # "k anchay", y "¿qué significa...?" no encontraba esas palabras.
    return texto_util.normalizar(texto)


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

    # Una pregunta de idioma nunca es una orden: "¿cómo se dice adiós?"
    # antes se tomaba como despedida y "¿qué significa menú?" como salir.
    if texto_util.es_pregunta_de_idioma(texto_normalizado):
        if any(
            texto_util.contiene_frase(texto_normalizado, marcador)
            for marcador in ("que significa", "que quiere decir", "significado de")
        ):
            return "significado"
        return "traducir"

    if texto_util.pide_orden(texto_normalizado, (
        "salir", "terminar", "adios", "hasta luego", "tupananchiskama",
        "nos vemos", "me voy", "menu", "volver al menu"
    )):
        return "salir"

    if texto_util.pide_orden(texto_normalizado, (
        "otra vez", "repite", "repetir", "siguiente", "continuar", "otra palabra"
    )):
        return "repetir"

    negado = bool({"no", "nunca"} & set(texto_normalizado.split()))

    if not negado and (
        _coincide_clave_intencion(
            texto_normalizado,
            ("enseñame", "enseñar")
        )
        or _coincide_clave_intencion(texto_normalizado, ("aprender",))
        or (
            _coincide_clave_intencion(texto_normalizado, ("muestrame", "mostrar"))
            and _coincide_clave_intencion(texto_normalizado, ("palabra", "quechua"))
        )
    ):
        return "aprender"

    if not negado and (
        _coincide_clave_intencion(texto_normalizado, ("practicar", "practica"))
        or _coincide_clave_intencion(texto_normalizado, ("preguntame",))
        or _coincide_clave_intencion(
            texto_normalizado,
            ("ejercicio", "prueba", "jugar")
        )
    ):
        return "practicar"

    if texto_util.pide_orden(texto_normalizado, ("traducir", "traduccion")):
        return "traducir"

    if texto_util.pide_orden(texto_normalizado, ("significado", "explicame")):
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

    if not os.path.isfile(ruta_db):
        print(f"[CONVERSACION] No existe el vocabulario: {ruta_db}")
        return None

    try:
        _conexion_vocabulario = sqlite3.connect(ruta_db)
    except sqlite3.Error as exc:
        print(f"[CONVERSACION] No se pudo abrir el vocabulario: {exc}")
        return None

    return _conexion_vocabulario


def _obtener_vocabulario_para_practica(conexion_db):
    """Todas las palabras del diccionario con quechua y español."""
    # Antes se buscaban las vocales como texto dentro de cada palabra; desde
    # que la búsqueda es por palabras completas eso ya no encuentra nada.
    try:
        registros = traductor._leer_registros_vocabulario(conexion_db)
    except Exception as exc:
        print(f"[CONVERSACION] No se pudo leer el vocabulario: {exc}")
        return []
    return [r for r in registros if r["quechua"] and r["espanol"]]


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
        "id": resultados.nueva_sesion(),
    }

    significado = registro["significado"] or "una palabra de uso cotidiano"
    return (
        f"Practiquemos una palabra. En quechua se dice "
        f"{registro['quechua']}. Significa {registro['espanol']}: "
        f"{significado}. Repítela, por favor."
    )


def _evaluar_respuesta(respuesta_usuario, respuesta_correcta):
    # Antes se aceptaban palabras distintas por parecido (wawa por Tawa).
    return texto_util.respuesta_quechua_correcta(
        respuesta_usuario,
        respuesta_correcta,
        pronunciaciones.variantes(respuesta_correcta)
    )


def _continuar_practica():
    global _sesion_educativa

    registro = _seleccionar_leccion()
    if registro is None:
        _sesion_educativa = None
        return "No pude cargar otra palabra del vocabulario local."

    # La misma práctica continúa con otra palabra: se conserva su identificador.
    id_sesion = (_sesion_educativa or {}).get("id") or resultados.nueva_sesion()
    _sesion_educativa = {
        "registro": registro,
        "estado": "esperando_repeticion",
        "id": id_sesion,
    }
    significado = registro["significado"] or "una palabra de uso cotidiano"
    return (
        f"Otra palabra: {registro['quechua']} significa "
        f"{registro['espanol']}, {significado}. Repítela, por favor."
    )


def pistas_practica():
    """Durante una práctica, la palabra a repetir y otras 5 del diccionario
    como pistas para el reconocedor de voz; fuera de la práctica, None."""
    if _sesion_educativa is None:
        return None
    pistas = [_sesion_educativa["registro"]["quechua"]]
    conexion_db = _obtener_conexion_vocabulario()
    if conexion_db is not None:
        otras = [r["quechua"] for r in _obtener_vocabulario_para_practica(conexion_db)
                 if r["quechua"] not in pistas and len(str(r["quechua"]).split()) <= 2]
        pistas += random.sample(otras, min(5, len(otras)))
    random.shuffle(pistas)
    return pistas


def _pantalla_sesion():
    """Palabra en práctica para mostrarla en pantalla (quechua y español)."""
    if _sesion_educativa is None:
        return None
    registro = _sesion_educativa["registro"]
    return {"content": registro["quechua"], "translation": registro["espanol"]}


def _palabra_sesion():
    """Palabra quechua en práctica, para hacer escuchar la voz de la docente."""
    if _sesion_educativa is None:
        return None
    return _sesion_educativa["registro"]["quechua"]


def _procesar_sesion_educativa(entrada):
    global _sesion_educativa

    if _sesion_educativa is None:
        return None

    entrada_normalizada = _normalizar_texto(entrada)

    # Una pregunta ("¿cómo se dice sol?") no es un intento de respuesta.
    if texto_util.es_pregunta_de_idioma(entrada_normalizada):
        return None

    intencion = _detectar_intencion(entrada)
    if intencion == "salir":
        _sesion_educativa = None
        return {
            "accion": "menu",
            "respuesta": "Terminamos por ahora. Tupananchiskama."
        }

    registro = _sesion_educativa["registro"]

    # "Repite" vuelve a decir la misma palabra; "otra vez" o "siguiente"
    # pasan a una nueva (antes "repite" cambiaba de palabra casi siempre).
    if texto_util.pide_orden(entrada_normalizada, ("repite", "repitelo", "repitela", "repetir")):
        return {
            "accion": "responder",
            "respuesta": (
                f"Escucha otra vez: {registro['quechua']}, que significa "
                f"{registro['espanol']}. Repítela, por favor."
            ),
            "pantalla": _pantalla_sesion(),
            "pronunciar": registro["quechua"],
        }

    if intencion == "repetir":
        return {
            "accion": "responder",
            "respuesta": _continuar_practica(),
            "pantalla": _pantalla_sesion(),
            "pronunciar": _palabra_sesion(),
        }

    es_correcta = _evaluar_respuesta(
        entrada,
        registro["quechua"]
    )
    _sesion_educativa["estado"] = "resultado"
    resultados.registrar_intento(
        "practica",
        registro["espanol"],
        registro["quechua"],
        entrada,
        es_correcta,
        _sesion_educativa.get("id"),
    )

    if es_correcta:
        respuesta = (
            f"Muy bien. Dijiste {registro['quechua']} correctamente. "
            "Di siguiente para practicar otra palabra, "
            "o salir para terminar."
        )
    else:
        respuesta = (
            f"Todavía no. La forma correcta es {registro['quechua']}. "
            "Inténtalo otra vez, di siguiente para cambiar de palabra, "
            "o salir para terminar."
        )

    return {
        "accion": "responder",
        "respuesta": respuesta,
        "pantalla": _pantalla_sesion(),
        # Si se equivocó, escucha cómo lo dice la docente (modo docente).
        "pronunciar": None if es_correcta else registro["quechua"],
    }


def _extraer_termino(entrada):
    return traductor.extraer_termino(entrada)


def _responder_consulta_local(entrada, idioma_entrada):
    consulta = _consulta_local(entrada, idioma_entrada)
    return consulta["respuesta"] if consulta else None


def _consulta_local(entrada, idioma_entrada):
    """Busca en el diccionario y devuelve la respuesta hablada y lo que debe
    verse en pantalla (palabra quechua y significado), o None."""
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
        opciones = resultado["resultados"][:3]
        return {
            "respuesta": traductor.describir_opciones(opciones),
            "pantalla": {
                "content": " / ".join(r["quechua"] for r in opciones),
                "translation": " / ".join(r["espanol"] for r in opciones),
            },
        }

    registro = resultado["resultados"][0]
    pantalla = {
        "content": registro["quechua"],
        "translation": registro["espanol"],
    }
    return {
        "respuesta": _texto_consulta(registro, idioma_entrada),
        "pantalla": pantalla,
        "pronunciar": registro["quechua"],
    }


def _texto_consulta(registro, idioma_entrada):
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


def _pide_otro_idioma(texto):
    """Yura solo enseña quechua (límite 5.4 de la tesis)."""
    tokens = set(_normalizar_texto(texto).split())
    return bool(tokens & {"ingles", "english", "frances", "portugues", "aleman"})


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
    if texto_normalizado in {"allin sukha", "allin sukay", "allin tuta"}:
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
        "cuando no entiendas. Si el estudiante habla de otro tema, responde "
        "con amabilidad en una frase y propón practicar una palabra en "
        "quechua. Nunca hables de temas inadecuados para niños."
    )

    vocabulario = traductor.vocabulario_relevante(
        entrada,
        _obtener_conexion_vocabulario()
    )
    if vocabulario:
        prompt_sistema += (
            "\n\nVocabulario quechua verificado del diccionario de Yura "
            "(español = quechua):\n"
            f"{traductor.formatear_vocabulario(vocabulario)}\n"
            "Cuando digas una palabra en quechua, usa SOLO las de esta lista. "
            "Si te piden una palabra que no está en la lista, di con cariño "
            "que todavía no está en tu diccionario y ofrece practicar otra "
            "de la lista. Nunca inventes palabras en quechua."
        )

    mensajes = [{"role": "system", "content": prompt_sistema}]
    if historial:
        mensajes.extend(historial[-8:])
    # Una transcripción enorme solo agrega costo y espera (Groq rechaza >8000 tokens).
    mensajes.append({"role": "user", "content": entrada[:500]})

    try:
        print("[CONVERSACION] Consultando Groq...")
        respuesta = traductor.consultar_modelo_groq(
            groq_client,
            mensajes,
            temperatura=0.7,
            max_tokens=300
        )

        if respuesta.choices and respuesta.choices[0].finish_reason == "length":
            print("[CONVERSACION] Aviso Groq: la respuesta llegó cortada.")

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
            "respuesta": _comenzar_practica(),
            "pantalla": _pantalla_sesion(),
            "pronunciar": _palabra_sesion(),
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
        consulta = _consulta_local(entrada_original, "espanol")
        if consulta:
            return {"accion": "responder", **consulta}

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
        consulta = _consulta_local(entrada_original, "quechua")
        if consulta:
            return {"accion": "responder", **consulta}

    # Una palabra suelta ("perro", "ñawi") se busca en el diccionario antes
    # de descartarla como tema ajeno ("no vendo autos...").
    if len(entrada.split()) <= 3:
        for idioma in ("espanol", "quechua"):
            consulta = _consulta_local(entrada_original, idioma)
            if consulta:
                return {"accion": "responder", **consulta}

    # Con Groq disponible, las frases de otros temas ("¿cómo estás?",
    # "¿qué sabes hacer?") las contesta Groq y vuelve al quechua; antes se
    # rechazaban casi todas con "no vendo autos ni converso en inglés".
    if _pide_otro_idioma(entrada_original) or (
        not groq_client and not _es_tema_quechua(entrada_original)
    ):
        return {
            "accion": "responder",
            "respuesta": (
                "Soy Yura, un robot educativo que ayuda a practicar quechua. "
                "Puedo enseñarte palabras, jugar contigo o decirte cómo se "
                "dice algo en quechua."
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
    depuracion.voz("[CONVERSACION] Usuario", entrada_para_groq)
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