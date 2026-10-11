"""Pruebas para el afinador acústico de Vosk (Kaldi) en quechua."""
import pytest
import pronunciaciones


def test_afinar_vosk_comandos_sistema():
    """Los comandos generales del sistema no deben ser alterados por el afinador."""
    assert pronunciaciones.afinar_vosk("jugar") == "jugar"
    assert pronunciaciones.afinar_vosk("traducir") == "traducir"
    assert pronunciaciones.afinar_vosk("conversar") == "conversar"
    assert pronunciaciones.afinar_vosk("menu") == "menu"
    assert pronunciaciones.afinar_vosk("volver al menu") == "volver al menu"
    assert pronunciaciones.afinar_vosk("apagate") == "apagate"
    assert pronunciaciones.afinar_vosk("silencio") == "silencio"
    assert pronunciaciones.afinar_vosk("si") == "si"
    assert pronunciaciones.afinar_vosk("no") == "no"


def test_afinar_vosk_palabras_docente():
    """Aproximaciones fonéticas registradas por Vosk deben convertirse al quechua exacto."""
    assert pronunciaciones.afinar_vosk("mi cuna") == "Mikhuna"
    assert pronunciaciones.afinar_vosk("comer") == "Q'umir"
    assert pronunciaciones.afinar_vosk("alcohol") == "Allqu"
    assert pronunciaciones.afinar_vosk("cada waldo") == "Kawallu"
    assert pronunciaciones.afinar_vosk("es kai") == "Iskay"
    assert pronunciaciones.afinar_vosk("esta agua") == "Tawa"
    assert pronunciaciones.afinar_vosk("entonces a") == "Phichqa"
    assert pronunciaciones.afinar_vosk("sara") == "Sara"


def test_afinar_vosk_texto_vacio_y_unk():
    assert pronunciaciones.afinar_vosk("") == ""
    assert pronunciaciones.afinar_vosk(None) == ""
    assert pronunciaciones.afinar_vosk("[unk]") == ""


def test_respuesta_aceptada_con_transcripcion_vosk():
    """El juego debe aceptar la respuesta tanto si viene cruda de Vosk como afinada."""
    # Vosk escuchó 'alcohol', la respuesta correcta esperada es 'Allqu'
    assert pronunciaciones.respuesta_aceptada("alcohol", "Allqu") is True
    # Vosk escuchó 'mi cuna', la respuesta correcta esperada es 'Mikhuna'
    assert pronunciaciones.respuesta_aceptada("mi cuna", "Mikhuna") is True
    # Vosk escuchó 'es kai', la respuesta correcta esperada es 'Iskay'
    assert pronunciaciones.respuesta_aceptada("es kai", "Iskay") is True


@pytest.mark.parametrize("escuchado", [
    # Lo que Vosk escribió en la Raspberry Pi al decir "apágate" (no la tiene
    # en su vocabulario) y "Yura, apágate" ("Yura" la escribe "jura"/"llora").
    "gate", "para date", "atada te", "atala te", "a paquete", "apaga paquete",
    "aparte", "llora a para ti", "jura paga te ya", "puedes a pagarte",
    "pues esa pagarte", "a paga te por favor", "jura apaga ti", "malaga gate", "para ti", "date",
])
def test_afinar_vosk_reconoce_apagate_deformado(escuchado):
    import texto as texto_util
    afinado = pronunciaciones.afinar_vosk(escuchado)
    assert afinado == "apagate"
    assert texto_util.es_orden_apagar(texto_util.normalizar(afinado))


@pytest.mark.parametrize("frase", [
    "la puerta de la casa", "para mi mama", "aparte de eso quiero jugar", "te quiero",
])
def test_afinar_vosk_no_confunde_frases_con_apagate(frase):
    assert pronunciaciones.afinar_vosk(frase) != "apagate"


def test_afinar_vosk_usa_ordenes_aprendidas(tmp_path, monkeypatch):
    import json
    ruta = tmp_path / "ordenes.json"
    ruta.write_text(json.dumps({"ordenes": {"chupar": "jugar", "lo raza": "apagate"}, "ambiguas": ["ya"]}))
    monkeypatch.setattr(pronunciaciones, "RUTA_ORDENES_VOSK", str(ruta))
    assert pronunciaciones.afinar_vosk("chupar") == "jugar"
    assert pronunciaciones.afinar_vosk("jura lo raza") == "apagate"
    assert pronunciaciones.afinar_vosk("ya") != "jugar"


def test_entrenar_ordenes_no_aprende_lo_riesgoso(tmp_path, monkeypatch):
    monkeypatch.setattr(pronunciaciones, "RUTA_ORDENES_VOSK", str(tmp_path / "no_existe.json"))
    from basedatos import entrenar_ordenes as e
    assert not e.puede_aprenderse("jugar", "jugar")         # ya lo escribe bien
    assert not e.puede_aprenderse("si", "apagate")          # es otra orden
    assert not e.puede_aprenderse("mi cuna", "jugar")       # es Mikhuna (quechua)
    assert not e.puede_aprenderse("gate", "apagate")        # ya se entiende
    assert not e.puede_aprenderse("te", "si")               # muy corto
    assert not e.puede_aprenderse("apaga te", "si")         # ya es apágate
    assert e.puede_aprenderse("chupar", "jugar")
    aprendidas = {}
    assert e.agregar(aprendidas, "chupar", "jugar")
    e.agregar(aprendidas, "chupar", "traducir")             # ambigua: se quita
    assert aprendidas["chupar"] is None


@pytest.mark.parametrize("escuchado, esperado", [
    # Modo castellano: lo que se pregunta "cómo se dice" es castellano.
    ("como se dice agua en quechua", "como se dice agua en quechua"),
    ("como se dice azul en quechua", "como se dice azul en quechua"),
    ("traduce agua", "traduce agua"),
    ("hola yura como estas", "hola yura como estas"),
    # Modo quechua: lo que se pregunta "qué significa" es quechua.
    ("que significa alcohol", "que significa Allqu"),
    # Respuestas de una palabra (juego): siguen afinándose.
    ("alcohol", "Allqu"),
    ("mi cuna", "Mikhuna"),
])
def test_afinar_vosk_separa_castellano_y_quechua(escuchado, esperado):
    assert pronunciaciones.afinar_vosk(escuchado) == esperado


def test_pregunta_de_idioma_se_responde_tras_afinar():
    import conversacion
    import texto as texto_util
    respuesta = conversacion.procesar_entrada(
        texto_util.normalizar(pronunciaciones.afinar_vosk("como se dice agua en quechua")), None
    )
    assert "yaku" in respuesta["respuesta"].lower()


def test_dentro_de_una_frase_no_cambia_palabras_castellanas_cortas():
    assert pronunciaciones.afinar_vosk("desde que") == "desde que"
    assert pronunciaciones.afinar_vosk("es kai") == "Iskay"  # patrón de dos palabras sí


def test_el_modo_de_idioma_se_mantiene_hasta_pedir_quechua():
    import conversacion
    conversacion.procesar_entrada("háblame en español", None)
    assert conversacion.MODO_IDIOMA["bilingue"] is True
    conversacion.procesar_entrada("como es", None)
    assert conversacion.MODO_IDIOMA["bilingue"] is True
    conversacion.procesar_entrada("háblame en quechua", None)
    assert conversacion.MODO_IDIOMA["bilingue"] is False


@pytest.mark.parametrize("pedazo", ["me", "la que", "de"])
def test_un_pedazo_de_frase_pide_repetir(pedazo):
    import conversacion
    assert "repites" in conversacion.procesar_entrada(pedazo, None)["respuesta"]


def test_repetir_la_palabra_ensenada_se_felicita():
    import conversacion
    conversacion.procesar_entrada("como se dice verde en quechua", None)
    assert "muy bien" in conversacion.procesar_entrada("homer no cumplir homer", None)["respuesta"].lower()


def test_quiero_que_me_digas_es_como_se_dice():
    import conversacion
    respuesta = conversacion.procesar_entrada("quiero que me digas quiero jugar", None)["respuesta"]
    assert "Pukllayta munani" in respuesta


def test_el_docente_se_mantiene_sin_repetirlo():
    import conversacion
    assert conversacion._habla_el_docente("estoy el docente")
    assert conversacion._habla_el_docente("ya pero no digas el resto")


def test_lista_por_tema_sale_del_diccionario():
    import conversacion
    respuesta = conversacion.procesar_entrada("como se dice los numeros del uno al nueve en quechua", None)["respuesta"]
    assert "Uj es uno" in respuesta and "Jisq'un es nueve" in respuesta
    colores = conversacion.procesar_entrada("dime los colores en quechua", None)["respuesta"]
    assert "Puka es rojo" in colores and "más" in colores
    mas = conversacion.procesar_entrada("si", None)["respuesta"]
    assert mas.startswith("Más de los colores") and "Puka" not in mas
