"""Órdenes de voz para mover el cuerpo de Yura (ESP32)."""
from unittest.mock import Mock

import pytest

import texto as texto_util
from main_robot import BrainYura


@pytest.mark.parametrize("frase, orden", [
    ("camina hacia adelante", "ADELANTE"), ("avanza", "ADELANTE"), ("avanzar", "ADELANTE"),
    ("camina hacia atrás", "ATRAS"), ("retrocede", "ATRAS"), ("retroceder", "ATRAS"),
    ("gira a la izquierda", "IZQUIERDA"), ("gira a la derecha", "DERECHA"), ("a la derecha", "DERECHA"),
    ("Yuraq avanza", "ADELANTE"), ("para", "ALTO"), ("detente", "ALTO"), ("detenerse", "ALTO"), ("alto", "ALTO"), ("Yura, para ya", "ALTO"),
])
def test_reconoce_ordenes_de_movimiento(frase, orden):
    assert texto_util.orden_movimiento(texto_util.normalizar(frase)) == orden


@pytest.mark.parametrize("frase", [
    "para mi mamá", "habla más alto", "no camines hacia adelante", "¿cómo se dice derecha?",
    "mi casa está a la derecha de la escuela", "la mano derecha y la izquierda", "gira", "",
])
def test_no_mueve_con_frases_comunes(frase):
    assert texto_util.orden_movimiento(texto_util.normalizar(frase)) is None


def _robot(escuchado, conectado=True):
    robot = object.__new__(BrainYura)
    robot.hw = Mock()
    robot.cuerpo = Mock(conectado=conectado)
    robot.escuchar_voz = Mock(return_value=escuchado)
    robot._normalizar_texto = texto_util.normalizar
    return robot


def test_avanzar_mueve_el_cuerpo_y_avisa():
    robot = _robot("camina hacia adelante")
    assert robot._escuchar_con_ordenes() == ""
    robot.cuerpo.mover.assert_called_once_with("ADELANTE", 1500)
    robot.hw.hablar.assert_called_once()


def test_detenerse_funciona_incluso_en_silencio():
    robot = _robot("detente")
    assert robot._escuchar_con_ordenes(solo_local=True, permitir_movimiento=False) == ""
    robot.cuerpo.alto.assert_called_once()
    robot.hw.hablar.assert_not_called()


def test_en_silencio_no_se_mueve():
    robot = _robot("camina hacia adelante")
    robot._escuchar_con_ordenes(solo_local=True, permitir_movimiento=False)
    robot.cuerpo.mover.assert_not_called()


def test_sin_cuerpo_conectado_avisa_y_no_mueve():
    robot = _robot("gira a la derecha", conectado=False)
    robot._escuchar_con_ordenes()
    robot.cuerpo.mover.assert_not_called()
    assert "cuerpo" in robot.hw.hablar.call_args.args[0]
