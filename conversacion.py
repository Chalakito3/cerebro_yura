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

    # Solo un pedido empieza la práctica: "me gusta jugar" o "jugué con mi
    # perro" cuentan algo, no la piden (antes Yura quedaba atrapada en la
    # práctica respondiendo "Todavía no" a todo; visto al medir, 07/10/2026).
    pide = bool(re.search(
        r"\b(quiero|queremos|vamos a|podemos|puedes|hagamos|juguemos|a)\s+(practicar|jugar|un ejercicio|una prueba)\b"
        r"|^(practicar|practiquemos|juguemos|jugar|preguntame|hazme una pregunta|ejercicio|prueba)\b",
        texto_normalizado,
    ))
    if not negado and pide:
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
    return pronunciaciones.respuesta_aceptada(respuesta_usuario, respuesta_correcta)


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




def quitar_frases_en_ingles(texto):
    """Compatibilidad: ahora lo hace texto.limpiar_respuesta_ia."""
    return texto_util.limpiar_respuesta_ia(texto)


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
    registro = _sesion_educativa["registro"]
    # "Tupananchiskama" es despedida, pero si es la palabra pedida es la respuesta.
    if intencion == "salir" and not _evaluar_respuesta(entrada, registro["quechua"]):
        _sesion_educativa = None
        return {
            "accion": "menu",
            "respuesta": "Terminamos por ahora. Tupananchiskama."
        }

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
    # "¿Qué me has querido decir?" es una pregunta, no un intento: se explica
    # lo que se pidió en vez de decir "Todavía no" (visto en vivo, 07/10/2026).
    palabras_dichas = set(entrada.split())
    saludo_o_castellano = palabras_dichas & (pronunciaciones._PALABRAS_CASTELLANAS | {"hola", "yura", "chau", "gracias", "buenas"})
    if not es_correcta and (len(saludo_o_castellano) >= 2 or (saludo_o_castellano and len(palabras_dichas) <= 2)):
        return {
            "accion": "responder",
            "respuesta": (
                f"Te pedí que repitas la palabra «{registro['quechua']}», que significa "
                f"{str(registro['espanol']).lower()}. ¿Lo intentas? Di: «{registro['quechua']}»."
            ),
            "pantalla": _pantalla_sesion(),
            "pronunciar": registro["quechua"],
        }
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
    _esperar_palabra(registro["quechua"])
    return {
        "respuesta": _texto_consulta(registro, idioma_entrada),
        "pantalla": pantalla,
        "pronunciar": registro["quechua"],
    }


# Palabra que Yura acaba de enseñar ("¿Me la repites? Di: «Q'umir»"): en los
# 30 s siguientes, lo que diga el estudiante se compara con ella (antes, el
# intento "homer" para Q'umir se mandaba a Groq y respondía sin sentido).
_PALABRA_ESPERADA = {"palabra": None, "hasta": 0.0, "intentos": 0}


def _esperar_palabra(palabra):
    import time
    _PALABRA_ESPERADA.update(palabra=palabra, hasta=time.monotonic() + 30, intentos=0)


def _intento_de_palabra(entrada_original, entrada):
    """Respuesta si el estudiante intentó repetir la palabra enseñada, o None."""
    import time
    palabra = _PALABRA_ESPERADA["palabra"]
    if not palabra or time.monotonic() > _PALABRA_ESPERADA["hasta"]:
        return None
    if texto_util.es_pregunta_de_idioma(entrada):
        return None  # pregunta otra cosa
    if _evaluar_respuesta(entrada_original, palabra) or any(
        _evaluar_respuesta(trozo, palabra) for trozo in entrada.split() if len(trozo) >= 3
    ):
        _PALABRA_ESPERADA["palabra"] = None
        return _variante(palabra + "bien", (
            f"¡Muy bien! Dijiste «{palabra}». ¿Quieres saber otra palabra?",
            f"¡Excelente! «{palabra}» te salió muy bien. Pregúntame otra cuando quieras.",
        ))
    # Una frase larga o en castellano ya es otra conversación; un intento corto, no.
    palabras = set(entrada.split())
    if len(entrada.split()) > 4 or len(palabras & (pronunciaciones._PALABRAS_CASTELLANAS | {"dime", "numeros"})) >= 2:
        _PALABRA_ESPERADA["palabra"] = None
        return None
    _PALABRA_ESPERADA["intentos"] += 1
    if _PALABRA_ESPERADA["intentos"] > 1:
        _PALABRA_ESPERADA["palabra"] = None
        return None
    return f"¡Buen intento! Escucha otra vez y repite despacio: «{palabra}»."


# Preguntas por tema ("los números del uno al nueve", "los colores"): la
# lista sale del diccionario de la base de datos (antes solo se buscaba una
# palabra suelta y Yura decía que no lo tenía; visto en vivo, 07/10/2026).
_TEMAS = {
    "numeros": "numeros", "colores": "colores", "animales": "animales", "frutas": "frutas",
    "comidas": "alimentos", "alimentos": "alimentos", "familia": "familia", "cuerpo": "partes_del_cuerpo",
    "saludos": "saludos", "verbos": "verbos", "lugares": "lugares", "pronombres": "pronombres",
    "utensilios": "utensilios_cocina", "herramientas": "herramientas", "escolares": "objetos_escolares",
    "naturaleza": "elementos_naturales", "preguntas": "preguntas",
}
_NOMBRE_TEMA = {
    "numeros": "los números", "colores": "los colores", "animales": "los animales", "frutas": "las frutas",
    "alimentos": "los alimentos", "familia": "la familia", "partes_del_cuerpo": "las partes del cuerpo",
    "saludos": "los saludos", "verbos": "algunos verbos", "lugares": "los lugares", "pronombres": "los pronombres",
    "utensilios_cocina": "los utensilios de cocina", "herramientas": "las herramientas",
    "objetos_escolares": "los objetos de la escuela", "elementos_naturales": "la naturaleza", "preguntas": "las preguntas",
}
_NUMEROS_ES = {
    "uno": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7, "ocho": 8, "nueve": 9,
    "diez": 10, "once": 11, "doce": 12, "trece": 13, "catorce": 14, "quince": 15, "veinte": 20,
}


# Para seguir la lista cuando dicen "sí" o "más" a "¿Quieres que te diga más?".
_ULTIMO_TEMA = {"tema": None, "desde": 0, "hasta": 0.0}


def _tema_pedido(entrada):
    palabras = entrada.split()
    # "los números", "las frutas", "la familia", "partes del cuerpo": con artículo,
    # para no confundir "¿cómo se dice familia?" (una palabra) con la lista.
    for i, palabra in enumerate(palabras):
        tema = _TEMAS.get(palabra)
        if tema and i > 0 and palabras[i - 1] in {"los", "las", "la", "del", "de"}:
            return tema
    return None


def _responder_tema(entrada):
    import time
    tema = _tema_pedido(entrada)
    desde_lista = 0
    if not tema and _ULTIMO_TEMA["tema"] and time.monotonic() < _ULTIMO_TEMA["hasta"] and (
        entrada in {"si", "ari", "mas", "dime mas", "si dime mas", "otras", "si por favor", "quiero mas"}
    ):
        tema, desde_lista = _ULTIMO_TEMA["tema"], _ULTIMO_TEMA["desde"]
    if not tema:
        return None
    try:
        registros = [r for r in traductor._leer_registros_vocabulario(_obtener_conexion_vocabulario())
                     if r["categoria"] == tema]
    except Exception:
        return None
    if not registros:
        return None
    registros.sort(key=lambda r: r["id"])
    titulo = _NOMBRE_TEMA.get(tema, "estas palabras")
    rango = re.search(r"del? (\w+) (?:al|hasta el|hasta) (\w+)", entrada)
    if tema == "numeros" and rango:
        desde = _NUMEROS_ES.get(rango.group(1)) or (int(rango.group(1)) if rango.group(1).isdigit() else 1)
        hasta = _NUMEROS_ES.get(rango.group(2)) or (int(rango.group(2)) if rango.group(2).isdigit() else 10)
        elegidos = registros[max(0, desde - 1):min(hasta, 20)]
        titulo = f"Los números del {rango.group(1)} al {rango.group(2)}"
        quedan = 0
    else:
        elegidos = registros[desde_lista:desde_lista + 6]
        quedan = len(registros) - desde_lista - len(elegidos)
        titulo = ("Más de " + titulo) if desde_lista else titulo[:1].upper() + titulo[1:]
    _ULTIMO_TEMA.update(tema=tema if quedan else None, desde=desde_lista + len(elegidos),
                        hasta=time.monotonic() + 60)
    lista = ", ".join(f"{r['quechua']} es {str(r['espanol']).lower()}" for r in elegidos)
    cierre = "¿Quieres que te diga más?" if quedan else "¿Los repetimos juntos?"
    return {
        "accion": "responder",
        "respuesta": f"{titulo} en quechua: {lista}. {cierre}",
        "pantalla": {
            "content": " · ".join(r["quechua"] for r in elegidos),
            "translation": " · ".join(str(r["espanol"]) for r in elegidos),
        },
    }


_PIDE_DECIR = re.compile(
    r"^(?:yura\s+)?(?:quiero que me digas|me puedes decir|puedes decirme|me dices|dime como se dice)\s+"
    r"(?:como se dice\s+)?(.+?)(?:\s+en quechua)?$"
)


def _variante(palabra, opciones):
    """Una de las formas de responder, siempre la misma para cada palabra
    (así la frase se puede guardar para el modo sin internet)."""
    import zlib
    return opciones[zlib.crc32(str(palabra).encode("utf-8")) % len(opciones)]


def _otra_de_la_categoria(registro):
    """Otra palabra del mismo tema, para proponer un reto ("¿y rojo?")."""
    try:
        registros = traductor._leer_registros_vocabulario(_obtener_conexion_vocabulario())
    except Exception:
        return None
    mismas = sorted(
        (r for r in registros
         if r["categoria"] == registro["categoria"] and r["quechua"] != registro["quechua"]
         and r["espanol"] and len(str(r["espanol"]).split()) <= 2 and "/" not in str(r["espanol"])),
        key=lambda r: str(r["quechua"]),
    )
    return _variante(registro["quechua"], mismas) if mismas else None


def _texto_consulta(registro, idioma_entrada):
    """Respuesta a "¿cómo se dice...?" / "¿qué significa...?": la palabra y
    una invitación a seguir (repetirla, usarla o un reto con otra del tema)."""
    quechua = registro["quechua"]
    if idioma_entrada == "espanol":
        termino = str(registro["espanol"]).lower()
        mayuscula = termino[:1].upper() + termino[1:]
        categoria = _normalizar_texto(registro["categoria"])
        otra = _otra_de_la_categoria(registro)
        reto = (f"¿Un reto? Pregúntame cómo se dice {str(otra['espanol']).lower()}." if otra else
                f"¿Me la repites? Di: «{quechua}».")
        if categoria == "colores":
            opciones = (
                f"En quechua, {termino} se dice {quechua}. Por ejemplo, si ves algo {termino} cerca de ti, señálalo y di: «{quechua}».",
                f"{mayuscula} es {quechua}. Por ejemplo, di «{quechua}» cuando veas algo de ese color. {reto}",
            )
        elif categoria == "saludos":
            opciones = (
                f"Para decir {termino}, usamos «{quechua}». Por ejemplo, salúdame ahora tú: «{quechua}».",
                f"{mayuscula} se dice «{quechua}». Por ejemplo, úsalo hoy con tu familia o tus compañeros.",
            )
        else:
            opciones = (
                f"En quechua se dice {quechua}, que significa {termino}. ¿Me la repites? Di: «{quechua}».",
                f"¡Buena pregunta! {mayuscula} se dice {quechua}. Repítela conmigo: «{quechua}».",
                f"{mayuscula} es {quechua} en quechua. {reto}",
            )
        return _variante(quechua, opciones)

    significado = str(registro["significado"] or "").strip().rstrip(".")
    explicacion = f" {significado}." if significado else ""
    espanol = str(registro["espanol"]).strip()
    espanol = espanol if espanol[-1:] in "?!." else espanol + "."
    opciones = (
        f"{quechua} significa {espanol}{explicacion} ¿La decimos juntos? «{quechua}».",
        f"¡Muy bien que preguntes! {quechua} significa {espanol}{explicacion}",
    )
    return _variante(quechua, opciones)


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


_FRASES_PIDE_ESPANOL = (
    "no entiendo", "no te entiendo", "no entendi", "no comprendo",
    "no le entiendo", "no lo entiendo", "que dijiste", "que dijistes",
    "no se que dijiste", "dimelo en español", "dime en español",
    "dilo en español", "hablame en español", "habla en español",
    "hablar en español", "puedes hablar en español",
    "puedes decirlo en español", "puedes hablarme en español",
    "explicamelo en español", "explicame en español", "repite en español",
    "responde en español", "respondeme en español", "en español por favor",
    "traducelo al español", "dilo en castellano", "habla en castellano",
    "hablame en castellano", "puedes hablar en castellano",
    "conversa en español", "conversame en español", "converse en español",
    "conversemos en español", "hablemos en español", "contesta en español",
    "contestame en español", "conversa en castellano",
    "conversame en castellano", "hablemos en castellano",
)

# Vosk suele deformar el verbo ("con del frame en español"), pero entiende
# bien "en español". Si la frase termina así, es un pedido de idioma, salvo
# que sea una pregunta de traducción ("¿cómo se dice hola en español?").
_PREGUNTAS_TRADUCCION = ("como se dice", "que significa", "como se escribe", "traduc")


_FRASES_PIDE_QUECHUA = (
    "hablame en quechua", "habla en quechua", "hablemos en quechua",
    "en quechua por favor", "volvamos al quechua", "solo en quechua",
    "puedes hablar en quechua", "qhichwapi rimay", "qhichwapi rimasun",
)

# Idioma de la conversación (07/10/2026): al pedir "háblame en español" Yura
# queda en modo bilingüe (responde en el idioma en que le hablan) hasta que
# le piden "háblame en quechua". Antes valía solo para una respuesta.
MODO_IDIOMA = {"bilingue": False}


def _pide_hablar_en_quechua(texto):
    texto_normalizado = _normalizar_texto(texto)
    return any(texto_util.contiene_frase(texto_normalizado, frase) for frase in _FRASES_PIDE_QUECHUA)


def _pide_hablar_en_espanol(texto):
    """El estudiante no entendió el quechua y pide que Yura aclare en
    español, aunque esté en modo inmersión (para no dejarlo sin ayuda)."""
    texto_normalizado = _normalizar_texto(texto)
    if any(
        texto_util.contiene_frase(texto_normalizado, frase)
        for frase in _FRASES_PIDE_ESPANOL
    ):
        return True
    if any(f in texto_normalizado for f in _PREGUNTAS_TRADUCCION):
        return False
    return texto_normalizado.endswith(("en español", "en castellano"))


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
        "ayuda", "ari", "mana", "allillan", "allillanmi", "allin", "allinmi",
        "kashan", "kashani", "kashanki", "kachkan", "kachkanki",
        "suti", "sutiymi", "sutiyki", "munani", "munanki", "kusisqa",
        "kuska", "yachaywasi", "mikhuy", "pukllay", "sulpayki", "yusulpayki",
        "tupananchiskama", "wawa", "wawacha", "allqu", "misi", "tata", "mama",
        "chiri", "rupay", "maymanta", "mashkha", "watayuq", "rimaykullayki"
    }
    if any(
        token in temas_permitidos or token.startswith(("traduc", "pronunci", "rima", "yacha"))
        for token in tokens
    ):
        return True
    return any(
        f" {_normalizar_texto(frase)} " in f" {texto_normalizado} "
        for frase in FRASES_QUECHUA_CONOCIDAS
    )


def _responder_frase_local(texto):
    texto_normalizado = _normalizar_texto(texto)
    modo_inmersion = os.environ.get("YURA_MODO_CONVERSAR", "quechua_puro").strip().lower() in ("quechua_puro", "quechua", "inmersion")

    if modo_inmersion:
        respuestas = {
            "si": "¡Kusa! Kusisqa kaspaqa sumaqtam yachakusun. Imata ruwayta munanki?",
            "no": "Ama llakikuychu, wawacha. Kuska yachakusun. Maymantataq kanki?",
            "ari": "¡Kusa! Kusisqa kaspaqa sumaqtam yachakusun. Imata ruwayta munanki?",
            "mana": "Ama llakikuychu, wawacha. Kuska yachakusun. Maymantataq kanki?",
            "hola": "¡Rimaykullayki, wawacha! Kusisqam kani qamwan rimaspa. Imataq sutiyki?",
            "rimaykullayki": "¡Rimaykullayki, wawacha! Kusisqam kani qamwan rimaspa. Imataq sutiyki?",
            "imaynalla": "¡Allillanmi kashani! Qamrí, allillanchu kashanki?",
            "imaynalla kachkanki": "¡Allillanmi kashani! Qamrí, allillanchu kashanki?",
            "allillanmi": "¡Ancha allinmi! Kusisqachu kashanki?",
            "allillanmi kashani": "¡Ancha allinmi! Kusisqachu kashanki?",
            "allinmi": "¡Ancha allinmi! Kusisqachu kashanki?",
            "imataq sutiyki": "Ñuqaqa Yura kani. Qamrí, imataq sutiyki?",
            "yusulpayki": "¡Qampaqpis sulpayki! Sumaqtam qhichwata rimanki.",
            "sulpayki": "¡Qampaqpis sulpayki! Sumaqtam qhichwata rimanki.",
            "gracias": "¡Qampaqpis sulpayki! Sumaqtam qhichwata rimanki.",
            "anchata munakuyki": "¡Ñuqapis anchata munakuyki, sumaq wawacha!",
            "anchata kuyayki": "¡Ñuqapis anchata kuyayki, sumaq wawacha!",
            "tupananchiskama": "¡Tupananchiskama, sumaq wawa! Allin p'unchay kachun.",
            "adios": "¡Tupananchiskama, sumaq wawa! Allin p'unchay kachun.",
        }
    else:
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



# Cómo enseña Yura (07/10/2026): más suelta y creativa, apoya al estudiante
# y al docente. Se agrega a las instrucciones de Groq en los dos modos.
_ESTILO_YURA = (
    "\n\nTu forma de ser: eres alegre, curiosa y paciente, como una compañera que juega mientras enseña. "
    "No repitas siempre las mismas frases: varía tus saludos, felicitaciones y preguntas. "
    "Para enseñar puedes, de vez en cuando: proponer una adivinanza muy corta, contar una mini historia de "
    "una o dos frases con una palabra quechua, o lanzar un pequeño reto (\"¿sabes cómo se dice...?\"). "
    "Las adivinanzas hazlas en español y que la respuesta sea una palabra quechua del vocabulario "
    "(por ejemplo: \"Tengo cuatro patas y ladro, ¿cómo me dicen en quechua?\", respuesta: Allqu); "
    "no inventes frases largas en quechua. "
    "Relaciona las palabras con la vida del niño: su familia, la escuela, la comida, los animales, el campo. "
    "Felicita cada intento aunque tenga errores; si se equivoca, no digas que está mal: muéstrale con cariño "
    "la forma correcta (\"se dice así: ...\") e invítalo a repetirla. "
    "Si el estudiante parece aburrido o responde muy corto, propón un juego o un tema nuevo. "
    "Si quien te habla dice que es docente, profesor o profesora, ayúdale con ideas breves y prácticas para "
    "su clase usando el vocabulario (una actividad, un juego o una pregunta para el grupo), en español. "
    "No describas tus emociones ni tus gestos: nada de *sonríe*, (feliz), \"me siento contenta\" ni emojis. "
    "Solo di lo que dirías en voz alta, directo al niño."
)


def _consultar_groq(entrada, groq_client, historial=None, forzar_espanol=False):
    if not groq_client:
        print(
            "[CONVERSACION] Error Groq: "
            "el cliente no está disponible."
        )
        return None

    modo_inmersion = (
        os.environ.get("YURA_MODO_CONVERSAR", "quechua_puro").strip().lower()
        in ("quechua_puro", "quechua", "inmersion")
        and not forzar_espanol
        and not MODO_IDIOMA["bilingue"]
    )
    if modo_inmersion:
        prompt_sistema = (
            "Eres Yura, un robot educativo amable que conversa NETAMENTE en quechua boliviano "
            "(Qhichwa simi) con estudiantes de sexto de primaria. Tu objetivo es la inmersión total en quechua. "
            "Responde SIEMPRE en quechua boliviano con calidez, sencillez y cariño, usando oraciones cortas (máximo dos frases). "
            "Usa sufijos afectivos y de cortesía (-cha, -lla, -mi, -ri). "
            "Al final de tu respuesta, haz SIEMPRE una pregunta sencilla en quechua para que el niño continúe la conversación. "
            "Si el niño habla en quechua, felicítalo (¡Kusa!, ¡Allinmi!, ¡Ancha allin!) y profundiza la charla. "
            "Si el niño duda o responde brevemente, anímalo con opciones sencillas en quechua. "
            "Nunca respondas en inglés ni en otro idioma ajeno. Nunca recomiendes comprar ni vender "
            "nada, ni hables de precios, dinero, tiendas, marcas o publicidad. No uses Markdown, listas ni explicaciones largas. "
            "Habla de forma fluida y clara para ser leída en voz alta. Nunca hables de temas inadecuados para niños. "
            "Si te piden varias palabras (por ejemplo animales o colores), nombra como máximo cinco y pregunta si quiere más. "
        )
    else:
        prompt_sistema = (
            "Eres Yura, un asistente educativo amable para estudiantes de sexto "
            "de primaria. Conversa naturalmente en espanol o quechua boliviano, "
            "usando el mismo idioma que el estudiante. Puedes mezclar ambos si "
            "el estudiante lo hace. Nunca respondas en ingles ni en otro idioma "
            "que no sea castellano o quechua. Nunca recomiendes comprar ni vender "
            "nada, ni hables de precios, dinero, tiendas, marcas o publicidad. Responde en una sola frase o como máximo "
            "dos frases cortas, claras, calidas y aptas para ser leidas en voz "
            "alta. No uses Markdown, listas ni explicaciones largas. "
            "Ayuda a practicar quechua sin convertir cada respuesta en una clase. "
            "No inventes traducciones ni afirmes datos dudosos; pide aclaracion "
            "cuando no entiendas. Si el estudiante habla de otro tema, responde "
            "con amabilidad en una frase y propón practicar una palabra en "
            "quechua. Nunca hables de temas inadecuados para niños. "
            "Si te piden varias palabras (por ejemplo animales o colores), nombra como máximo cinco y pregunta si quiere más. "
        )
        if forzar_espanol:
            prompt_sistema += (
                "\n\nEl estudiante te pidió que le hables en español porque no "
                "entendió el quechua. Respóndele en español, con calidez, y "
                "anímalo a seguir practicando quechua cuando quiera."
            )

    prompt_sistema += _ESTILO_YURA

    vocabulario = traductor.vocabulario_relevante(
        entrada,
        _obtener_conexion_vocabulario()
    )
    if vocabulario:
        prompt_sistema += (
            "\n\nVocabulario quechua verificado del diccionario de Yura "
            "(español = quechua):\n"
            f"{traductor.formatear_vocabulario(vocabulario)}\n"
            "Arma tus frases en quechua SOLO con estas palabras y frases del diccionario de Yura "
            "(puedes agregarles sufijos comunes como -mi, -chu, -ta, -pi, -qa, -lla, -cha, -kuna). "
            "No uses palabras quechuas que no estén en la lista. "
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
            temperatura=0.85,  # más variada y creativa (antes 0.7)
            max_tokens=300
        )

        if respuesta.choices and respuesta.choices[0].finish_reason == "length":
            print("[CONVERSACION] Aviso Groq: la respuesta llegó cortada.")

        contenido = str(
            respuesta.choices[0].message.content or ""
        ).strip()

        contenido = texto_util.limpiar_respuesta_ia(contenido)
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


_FRASES_DOCENTE = (
    "soy la profesora", "soy el profesor", "soy profesora", "soy profesor", "soy la docente",
    "soy el docente", "soy docente", "soy la maestra", "soy el maestro", "soy maestra", "soy maestro",
    # Vosk a veces escribe "estoy" por "soy" (visto en vivo, 07/10/2026).
    "estoy el docente", "estoy la docente", "estoy el profesor", "estoy la profesora",
    "habla el docente", "habla la profesora", "habla el profesor",
    "para mi clase", "a mi clase", "con mi clase", "mis estudiantes", "mis alumnos", "a los estudiantes",
    "a los niños", "idea para la clase", "actividad para",
)
_PALABRAS_CREATIVAS = ("adivinanza", "adivinanzas", "cuento", "cuentito", "historia", "cancion", "chiste", "poema", "trabalenguas")


# Cuando habla el docente, Yura se queda en "modo docente" mientras siga la
# charla (antes, en la frase siguiente volvía al quechua para niños).
MINUTOS_MODO_DOCENTE = 5


def _habla_el_docente(texto):
    import time
    texto_normalizado = _normalizar_texto(texto)
    if any(texto_util.contiene_frase(texto_normalizado, frase) for frase in _FRASES_DOCENTE):
        MODO_IDIOMA["docente_hasta"] = time.monotonic() + 60 * MINUTOS_MODO_DOCENTE
        return True
    if time.monotonic() < MODO_IDIOMA.get("docente_hasta", 0):
        MODO_IDIOMA["docente_hasta"] = time.monotonic() + 60 * MINUTOS_MODO_DOCENTE
        return True
    return False


def _pide_algo_creativo(texto):
    return bool(set(_normalizar_texto(texto).split()) & set(_PALABRAS_CREATIVAS))


# Palabras que solas no son una pregunta: Vosk captó un pedazo de la frase
# ("me", "la que"); antes se buscaban en el diccionario (visto en vivo).
_SOLO_PEDAZO = {
    "me", "te", "se", "la", "el", "lo", "los", "las", "le", "les", "de", "del", "que", "y", "a",
    "en", "un", "una", "o", "e", "es", "al", "con", "por", "para", "mi", "tu", "su", "ya", "eh", "ah",
}


def procesar_entrada(entrada, groq_client, historial=None):
    global _sesion_educativa
    entrada_original = str(entrada or "").strip()
    # No se toca una pregunta: "¿qué significa imaynalla kachkanki?" quedaba
    # como solo "imaynalla kachkanki" y Yura saludaba en vez de explicar.
    if not texto_util.es_pregunta_de_idioma(_normalizar_texto(entrada_original)):
        entrada_original = _corregir_repeticion_quechua(entrada_original)
    entrada = _normalizar_texto(entrada_original)

    if entrada == "":
        return {
            "accion": "responder",
            "respuesta": "No logré escucharte."
        }

    # En una práctica, decir la palabra pedida es la respuesta, aunque también
    # sea un saludo ("Sulpayki"), un "sí" ("Ari") o parezca un pedazo de frase
    # ("Para", lluvia): antes esas 10 palabras no se podían acertar.
    if _sesion_educativa and _sesion_educativa.get("registro") and _evaluar_respuesta(
        entrada_original, _sesion_educativa["registro"]["quechua"]
    ):
        resultado_sesion = _procesar_sesion_educativa(entrada_original)
        if resultado_sesion is not None:
            return resultado_sesion

    # "Quiero que me digas «quiero jugar»" pide cómo se dice, no empieza a jugar.
    pide = _PIDE_DECIR.match(entrada)
    if pide:
        entrada_original = entrada = f"como se dice {pide.group(1)} en quechua"

    intento = _intento_de_palabra(entrada_original, entrada)
    if intento:
        return {"accion": "responder", "respuesta": intento}

    tema = _responder_tema(entrada)
    if tema:
        return tema

    if entrada in {"como se dice", "como digo", "que significa", "que quiere decir", "traduce"}:
        return {"accion": "responder",
                "respuesta": "¿Qué palabra quieres saber? Por ejemplo: «¿Cómo se dice perro en quechua?»"}

    if set(entrada.split()) <= _SOLO_PEDAZO:
        return {"accion": "responder", "respuesta": "No te escuché bien. ¿Me lo repites?"}

    if _pide_hablar_en_quechua(entrada_original):
        MODO_IDIOMA["bilingue"] = False
        MODO_IDIOMA["docente_hasta"] = 0
        return {"accion": "responder", "respuesta": "¡Ari! Qhichwapi rimasun. Imaynalla kashanki?"}

    if _pide_hablar_en_espanol(entrada_original):
        MODO_IDIOMA["bilingue"] = True
        respuesta = (
            _consultar_groq(entrada_original, groq_client, historial, forzar_espanol=True)
            if groq_client else None
        )
        return {
            "accion": "responder",
            "respuesta": respuesta or (
                "Perdón, te lo digo en español: dime qué palabra en quechua "
                "quieres practicar, o pregúntame cómo se dice algo."
            )
        }

    # "¿Qué significa imataq sutiyki?" pide la explicación, no que Yura diga
    # su nombre: las frases de saludo solo se contestan si no es una pregunta.
    respuesta_local = None if texto_util.es_pregunta_de_idioma(entrada) else _responder_frase_local(entrada_original)
    if respuesta_local:
        return {
            "accion": "responder",
            "respuesta": respuesta_local
        }

    # El docente pide ideas de clase, o alguien pide una adivinanza, cuento o
    # canción: lo contesta Groq (y se deja la práctica en curso), en vez de
    # tomarlo como respuesta de la práctica o empezar una ("enseñar").
    docente = _habla_el_docente(entrada_original)
    if docente or _pide_algo_creativo(entrada_original):
        _sesion_educativa = None
        pedido = (f"(Te habla la docente; respóndele en español con ideas para su clase.) {entrada_original}"
                  if docente else entrada_original)
        respuesta = _consultar_groq(pedido, groq_client, historial, forzar_espanol=docente) if groq_client else None
        return {
            "accion": "responder",
            "respuesta": respuesta or (
                "Me encantaría ayudarte con eso, pero ahora no tengo conexión. "
                "Mientras tanto, ¿practicamos una palabra en quechua?"
            ),
        }

    # En plena práctica, una frase de 3 o más palabras que no es la respuesta
    # ("estoy cansado de esto", "¿cómo estás tú?") es conversación: se sale de
    # la práctica y se contesta normal.
    if (_sesion_educativa and _sesion_educativa.get("registro") and len(entrada.split()) >= 3
            and not _evaluar_respuesta(entrada_original, _sesion_educativa["registro"]["quechua"])
            and not _detectar_intencion(entrada) in {"repetir", "salir"}):
        _sesion_educativa = None

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

    # "¿Qué significa imataq sutiyki?" pide la explicación, no que Yura diga
    # su nombre: las frases de saludo solo se contestan si no es una pregunta.
    respuesta_local = None if texto_util.es_pregunta_de_idioma(entrada) else _responder_frase_local(entrada_original)
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