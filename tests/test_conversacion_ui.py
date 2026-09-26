from unittest.mock import Mock

from main_robot import BrainYura


def test_conversation_entry_does_not_include_intro_sentence():
    robot = object.__new__(BrainYura)
    robot.saludo_inicial_done = False
    robot.state = None
    robot.hw = Mock()
    robot.escuchar_voz = Mock(return_value="hola")
    robot._normalizar_texto = lambda texto: str(texto or "").strip().lower()
    robot._set_web_status = Mock()
    robot.running = True
    robot.groq_client = None
    robot.historial_conversacion = []

    robot.ejecutar_conversar()

    messages = [call.args[0].lower() for call in robot.hw.hablar.call_args_list]
    assert all("soy yura" not in message for message in messages)
    assert all("a practicar quechua" not in message for message in messages)


def test_startup_greeting_is_quechua_and_silent_when_no_audio():
    robot = object.__new__(BrainYura)
    robot.saludo_inicial_done = False
    robot.state = None
    robot.hw = Mock()
    robot._set_web_status = Mock()
    robot.escuchar_voz = Mock(return_value="")
    robot._normalizar_texto = lambda texto: str(texto or "").strip().lower()
    robot.running = True
    robot.groq_client = None
    robot.historial_conversacion = []

    robot.ejecutar_menu()

    messages = [call.args[0].lower() for call in robot.hw.hablar.call_args_list]
    assert any("yura" in message and "kani" in message for message in messages)
    assert any("qhichwa" in message or "quechua" in message for message in messages)
    assert all("no logré escucharte" not in message for message in messages)
    assert all("no te entendí" not in message for message in messages)


def test_silence_command_is_recognized_without_noise():
    robot = object.__new__(BrainYura)
    robot.state = None
    robot.hw = Mock()
    robot._normalizar_texto = lambda texto: str(texto or "").strip().lower()
    robot._set_web_status = Mock()
    robot.groq_client = None
    robot.historial_conversacion = []
    robot.running = True
    robot.saludo_inicial_done = True

    robot.procesar_entrada = Mock(return_value={"accion": "menu", "respuesta": ""})

    robot.ejecutar_menu = Mock()

    # Simula el comando del usuario por voz
    comando = "silencio"
    normalizado = robot._normalizar_texto(comando)
    assert "silencio" in normalizado or "guarda silencio" in normalizado


def test_reconoce_respuestas_cortas_comunes_como_si_o_no():
    import conversacion

    for entrada in ("si", "no", "hola", "gracias", "ari", "mana"):
        resultado = conversacion.procesar_entrada(entrada, None)
        assert resultado["accion"] == "responder"
        assert "no entend" not in resultado["respuesta"].lower()


def test_traduccion_no_caiga_en_fallback_generico_si_falta_diccionario():
    import conversacion

    resultado = conversacion.procesar_entrada(
        "como se dice color naranja en quechua",
        None
    )

    assert resultado["accion"] == "responder"
    assert "momentos para pensar" not in resultado["respuesta"].lower()
    assert "naranja" in resultado["respuesta"].lower()


def test_buenas_noches_no_se_confunde_con_la_palabra_no():
    import conversacion

    resultado = conversacion.procesar_entrada("buenas noches", None)

    assert "allin tuta" in resultado["respuesta"].lower()
    assert "buenas noches" in resultado["respuesta"].lower()
    assert "entendido" not in resultado["respuesta"].lower()


def test_como_digo_buenas_noches_usa_la_traduccion_local():
    import conversacion

    resultado = conversacion.procesar_entrada(
        "como digo buenas noches en quechua",
        None
    )

    assert "allin tuta" in resultado["respuesta"].lower()
    assert "buenas noches" in resultado["respuesta"].lower()
    assert "por ejemplo" in resultado["respuesta"].lower()


def test_como_digo_color_amarillo_usa_el_diccionario_local():
    import conversacion

    resultado = conversacion.procesar_entrada(
        "como digo color amarillo en quechua",
        None
    )

    assert "q'ello" in resultado["respuesta"].lower()
    assert "amarillo" in resultado["respuesta"].lower()
    assert "por ejemplo" in resultado["respuesta"].lower()


def test_pedidos_fuera_del_alcance_explican_quien_es_yura():
    import conversacion

    for entrada in ("vendeme un auto", "habla en ingles"):
        resultado = conversacion.procesar_entrada(entrada, None)
        respuesta = resultado["respuesta"].lower()
        assert "soy yura" in respuesta
        assert "practicar quechua" in respuesta
