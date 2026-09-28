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
