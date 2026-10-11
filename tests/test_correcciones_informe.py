"""Regresiones de privacidad, validación y exportación del informe 30/09."""
import csv
import io
from types import SimpleNamespace

import pytest

import resultados
import web.app as web


@pytest.mark.parametrize('activo', [False, True])
@pytest.mark.parametrize('acceso', ['local', 'remoto', 'correcta', 'incorrecta', 'host_ajeno'])
def test_estado_sensible_solo_para_docente(monkeypatch, activo, acceso):
    resultados.definir_participante('Alumno Prueba')
    robot = SimpleNamespace(
        state=web.RobotStates.CONVERSAR, running=True,
        get_web_status=lambda: dict(phase='HABLANDO', content='Respuesta privada',
                                   translation='Texto privado', result='CORRECTO'),
    ) if activo else None
    monkeypatch.setattr(web, 'robot', robot)
    monkeypatch.setenv('YURA_RESULTADOS_CLAVE', 'clave-prueba')
    opciones = {}
    if acceso in ('remoto', 'correcta', 'incorrecta'):
        opciones['environ_overrides'] = {'REMOTE_ADDR': '192.168.1.50'}
    if acceso == 'host_ajeno':
        opciones['base_url'] = 'http://dominio-ajeno.example'
    if acceso in ('correcta', 'incorrecta'):
        opciones['auth'] = ('docente', 'clave-prueba' if acceso == 'correcta' else 'otra')
    respuesta = web.app.test_client().get('/api/status', **opciones)
    assert respuesta.status_code == 200
    assert respuesta.headers['Cache-Control'] == 'no-store'
    datos = respuesta.get_json()
    if acceso in ('local', 'correcta'):
        assert datos['participante'] == 'Alumno Prueba'
        if activo:
            assert datos['content'] == 'Respuesta privada'
    else:
        assert datos['participante'] == datos['content'] == datos['translation'] == ''
        assert datos['result'] is None
        assert 'Alumno Prueba' not in respuesta.text


@pytest.mark.parametrize('valor', ['=1+1', '+1+1', '-1+1', '@SUM(A1)', '  =1+1', '\t=1+1', 'allqu', "p'unchay"])
def test_csv_neutraliza_formulas_sin_cambiar_base(valor):
    resultados.registrar_intento('juego', valor, valor, valor, False, valor)
    respuesta = web.app.test_client().get('/resultados.csv')
    filas = list(csv.reader(io.StringIO(respuesta.text.lstrip('\ufeff'))))
    esperado = "'" + valor.strip() if valor.strip().startswith(('=', '+', '-', '@')) else valor
    for columna in (5, 6, 7):
        assert filas[1][columna] == esperado
    assert resultados.todos_los_intentos()[0]['respuesta'] == valor.strip()
    assert respuesta.headers['Cache-Control'] == 'no-store'


@pytest.mark.parametrize('ruta', ['/api/ensenar/voz', '/api/ensenar/grabar'])
@pytest.mark.parametrize('contenido', ['[1]', '[]', 'null', 'true', '12', '"texto"', '{'])
def test_json_invalido_devuelve_400(ruta, contenido):
    respuesta = web.app.test_client().post(ruta, data=contenido, content_type='application/json')
    assert respuesta.status_code == 400
    assert respuesta.get_json()['error']


@pytest.mark.parametrize('identificador', [True, False, 1.5, [], {}, None, -1, 0])
def test_identificador_invalido_no_consulta_base(monkeypatch, identificador):
    def inesperado(*args):
        pytest.fail('No debe consultar el diccionario con identificadores inválidos')
    monkeypatch.setattr(web.pronunciaciones, 'palabra_del_diccionario', inesperado)
    respuesta = web.app.test_client().post('/api/ensenar/voz', json={
        'tabla': 'nivel1_numeros', 'id': identificador, 'texto': 'Tawa',
    })
    assert respuesta.status_code == 400


@pytest.mark.parametrize('texto', [None, 123, [], {}, 'a' * 81])
def test_voz_rechaza_texto_invalido(texto):
    respuesta = web.app.test_client().post('/api/ensenar/voz', json={
        'tabla': 'nivel1_numeros', 'id': 1, 'texto': texto,
    })
    assert respuesta.status_code == 400
