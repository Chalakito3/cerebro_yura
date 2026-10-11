from types import SimpleNamespace

import conversacion
import traductor


def _cliente_que_captura(mensajes_capturados, respuesta="Q'ello"):
    def create(**kwargs):
        mensajes_capturados.extend(kwargs["messages"])
        return SimpleNamespace(choices=[SimpleNamespace(
            finish_reason="stop",
            message=SimpleNamespace(content=respuesta)
        )])

    return SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))
    )


def test_vocabulario_incluye_palabra_mencionada_y_saludos():
    conexion = conversacion._obtener_conexion_vocabulario()
    registros = traductor.vocabulario_relevante(
        "como se dice amarillo en quechua",
        conexion
    )
    quechua = {registro["quechua"] for registro in registros}

    assert "Q'illu" in quechua
    assert "Allin tuta" in quechua


def test_vocabulario_incluye_todo_el_tema_nombrado():
    conexion = conversacion._obtener_conexion_vocabulario()
    registros = traductor.vocabulario_relevante(
        "quiero aprender los colores",
        conexion
    )

    assert sum(r["categoria"] == "colores" for r in registros) >= 10


def test_conversacion_envia_vocabulario_verificado_a_groq():
    mensajes = []
    conversacion._consultar_groq(
        "como se dice amarillo",
        _cliente_que_captura(mensajes)
    )

    sistema = mensajes[0]["content"]
    assert "Amarillo = Q'illu" in sistema
    assert "Nunca inventes palabras en quechua" in sistema


def test_traductor_online_envia_vocabulario_verificado_a_groq():
    mensajes = []
    traductor.traducir_online(
        "amarillo",
        _cliente_que_captura(mensajes),
        conversacion._obtener_conexion_vocabulario()
    )

    assert "Amarillo = Q'illu" in mensajes[0]["content"]


def test_padre_y_papa_se_dicen_tata():
    conexion = conversacion._obtener_conexion_vocabulario()

    assert traductor.consultar_diccionario_local("padre", conexion) == "Tata"
    opciones = traductor.buscar_vocabulario("papá", "espanol", conexion)
    assert "Tata" in {registro["quechua"] for registro in opciones["resultados"]}


def test_traductor_dice_todas_las_opciones_si_la_palabra_es_ambigua():
    dichos = []
    entradas = iter(["papa", "salir"])

    traductor.ejecutar_traducir(
        lambda: next(entradas),
        dichos.append,
        conversacion._obtener_conexion_vocabulario(),
        None,
        lambda: True
    )

    assert "se dice Tata" in dichos[0]
    assert "se dice Papa" in dichos[0]


def test_busqueda_tolera_una_letra_si_es_unica():
    import sqlite3
    import traductor
    conexion = sqlite3.connect(":memory:")
    conexion.execute("CREATE TABLE nivel1_colores (id INTEGER PRIMARY KEY, palabra_frase TEXT, pronunciacion TEXT, traduccion TEXT, significado TEXT)")
    conexion.executemany("INSERT INTO nivel1_colores VALUES (?, ?, NULL, ?, NULL)",
                         [(1, "Q'umir", "Verde"), (2, "Puka", "Rojo"), (3, "Ch'uspi", "Mosca"), (4, "Ch'uspi", "Mesca")])
    assert [r["quechua"] for r in traductor.buscar_vocabulario("verdi", "espanol", conexion)["resultados"]] == ["Q'umir"]
    assert not traductor.buscar_vocabulario("rojj", "espanol", conexion)["encontrado"]       # muy corta
    assert not traductor.buscar_vocabulario("masca", "espanol", conexion)["encontrado"]      # dos parecidas


def test_extraer_termino_con_quechua_cortado():
    import traductor
    assert traductor.extraer_termino("cómo se dice perro en que") == "perro"
    assert traductor.extraer_termino("cómo se dice perro en quechu") == "perro"
    assert traductor.extraer_termino("cómo se dice queso") == "queso"


def test_quita_frases_en_ingles():
    import conversacion
    texto = "¿Puedes decirme qué significa ayinsuka? If no, we can practice another word."
    assert conversacion.quitar_frases_en_ingles(texto) == "¿Puedes decirme qué significa ayinsuka?"
    assert conversacion.quitar_frases_en_ingles("Allin p'unchay significa buenos días.") == "Allin p'unchay significa buenos días."


import pytest


@pytest.mark.parametrize("respuesta, esperado", [
    ("Hola. If no, we can practice another word.", "Hola."),
    ("Puedes comprar un libro en la tienda. Allqu significa perro.", "Allqu significa perro."),
    ("Hello! Yaku significa agua.", "Yaku significa agua."),
    ("Merci beaucoup. Muy bien.", "Muy bien."),
    ("Você fala bem. Sigamos.", "Sigamos."),
    ("Ese juguete cuesta poco, págalo. Sigamos.", "Sigamos."),
])
def test_quita_otros_idiomas_y_compras(respuesta, esperado):
    import texto
    assert texto.limpiar_respuesta_ia(respuesta) == esperado


@pytest.mark.parametrize("respuesta", [
    "Uya significa cara.",
    "Me cuesta comprender esa palabra, repítela.",
    "Mañana vendrá otra palabra nueva.",
    "Allin p'unchay significa buenos días.",
])
def test_no_quita_frases_inocentes(respuesta):
    import texto
    assert texto.limpiar_respuesta_ia(respuesta) == respuesta


def test_extraer_termino_con_pregunta_repetida():
    import traductor
    assert traductor.extraer_termino("cómo se dice, cómo se dice cómo estás") == "como estas"
    assert traductor.extraer_termino("qué significa qué significa wasi") == "wasi"


@pytest.mark.parametrize("respuesta, esperado", [
    # Groq lo dijo en vivo (11/10/2026): «pukllay bola» no existe.
    ("¡Qué divertido! En quechua, “fútbol” se dice “pukllay bola”. ¿Quieres jugar?",
     "¡Qué divertido! Esa palabra todavía no está en mi diccionario. ¿Quieres jugar?"),
    ("En quechua, computadora es antanikiq. Vamos a practicar.",
     "Esa palabra todavía no está en mi diccionario. Vamos a practicar."),
    ("Perro se dice en quechua bolatay.", "Esa palabra todavía no está en mi diccionario."),
])
def test_quita_traducciones_que_no_estan_en_el_diccionario(respuesta, esperado):
    assert conversacion.quitar_traducciones_inventadas(respuesta) == esperado


@pytest.mark.parametrize("respuesta", [
    "¡Buena pregunta! Perro se dice Allqu. Repítela conmigo: «Allqu».",
    "Gato se dice Misi y perro se dice Allqu.",
    "Perro se dice en quechua Allqu.",
    "Se dice así: Allillanmi. ¡Muy bien!",
    "\"Allqu\" significa perro.",
    "¿Sabes cómo se dice perro en quechua?",
    "Se dice que los incas hablaban quechua.",
    "Allqu se dice en español perro.",
    "Eso significa que estás aprendiendo mucho.",
    "Rimaykullayki! Imaynalla kachkanki?",
])
def test_deja_las_palabras_del_diccionario_y_el_castellano(respuesta):
    assert conversacion.quitar_traducciones_inventadas(respuesta) == respuesta


def test_groq_no_puede_ensenar_palabras_inventadas():
    mensajes = []
    cliente = _cliente_que_captura(mensajes, respuesta="¡Qué bien! Fútbol se dice pukllay bola.")
    respuesta = conversacion._consultar_groq("me gusta jugar futbol", cliente)

    assert "pukllay bola" not in respuesta
    assert "todavía no está en mi diccionario" in respuesta


@pytest.mark.parametrize("respuesta, esperado", [
    # En vivo (11/10/2026) la negrita quedaba «se dice * * en quechua».
    ("Tu perro es muy grande, se dice **Allqu jatun** en quechua.",
     "Tu perro es muy grande, se dice Allqu jatun en quechua."),
    ("*sonríe feliz* ¡Kusa, qamri! 😊 (contenta) Imataq munanki?", "¡Kusa, qamri! Imataq munanki?"),
    ("Se dice *Misi* en quechua.", "Se dice Misi en quechua."),
    ("[risas] Allqu es lindo.", "Allqu es lindo."),
])
def test_quita_gestos_pero_no_las_palabras_resaltadas(respuesta, esperado):
    import texto as texto_util
    assert texto_util.limpiar_respuesta_ia(respuesta) == esperado
