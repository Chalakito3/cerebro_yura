import io
import json
import os
import random
import urllib.error

import pytest

import laravel_actividades as la

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DICCIONARIO = os.path.join(RAIZ, "diccionario.db")


def _actividad(respondientes=(103, 101), por_respondiente=1, categoria="nivel1_colores"):
    """El ejemplo del contrato v1.2."""
    return {
        "activity_id": "0199c204-5f70-7aa1-8d47-e4b1a7bb0925",
        "attempt_id": "0199c204-5f70-7aa1-8d47-e4b1a7bb0930",
        "attempt_number": 1,
        "content": {"category": categoria},
        "grading_target": {"quarter": 1, "activity_number": 2, "type": "robot"},
        "groups": [{
            "group_id": "0199c204-6ae7-7553-90d4-e5d9592bc776",
            "members": [
                {"student_id": 101, "display_name": "María"},
                {"student_id": 102, "display_name": "Luis"},
                {"student_id": 103, "display_name": "Ana"},
            ],
            "respondent_student_ids": list(respondientes),
        }],
        "execution": {"group_size": 20, "respondents_per_group": len(respondientes),
                      "questions_per_respondent": por_respondiente},
    }


class ClienteFalso:
    def __init__(self, estados=None, codigo_envio=201):
        self.estados = list(estados or [])
        self.codigo_envio = codigo_envio
        self.enviados = []

    def estado(self, activity_id, attempt_id):
        return self.estados.pop(0) if self.estados else "in_progress"

    def enviar(self, resumen):
        self.enviados.append(resumen)
        if self.codigo_envio == "red":
            raise la.ErrorRed("sin red")
        return self.codigo_envio


def _ejecutor(tmp_path, cliente, respuestas_oidas):
    dichas = []
    oidas = list(respuestas_oidas)
    preguntas = []

    def escuchar(pistas):
        return oidas.pop(0) if oidas else ""

    ejecutor = la.EjecutorActividad(
        cliente, la.Outbox(str(tmp_path / "outbox")), hablar=dichas.append, escuchar=escuchar,
        mostrar=lambda nombre, pregunta: preguntas.append((nombre, pregunta)),
        ruta_db=DICCIONARIO, azar=random.Random(1),
    )
    return ejecutor, dichas, preguntas


# ------------------------------------------------------------ configuración

def test_url_https_o_red_privada():
    assert la.url_permitida("https://demo.trycloudflare.com")
    assert la.url_permitida("http://192.168.1.20:8000")
    assert la.url_permitida("http://localhost:8000")
    assert not la.url_permitida("http://demo.trycloudflare.com")
    assert not la.url_permitida("ftp://192.168.1.20")


def test_sincronizacion_apagada_por_defecto(monkeypatch):
    monkeypatch.delenv("YURA_LARAVEL_SYNC_ENABLED", raising=False)
    monkeypatch.setenv("YURA_LARAVEL_URL", "https://demo.example")
    monkeypatch.setenv("YURA_LARAVEL_TOKEN", "x")
    assert la.configuracion() is None


@pytest.mark.parametrize("url, token", [
    ("", "x"), ("https://demo.example", ""), ("https://demo.example/api", "x"), ("http://demo.example", "x"),
])
def test_configuracion_incompleta_o_insegura_no_sincroniza(monkeypatch, url, token):
    monkeypatch.setenv("YURA_LARAVEL_SYNC_ENABLED", "1")
    monkeypatch.setenv("YURA_LARAVEL_URL", url)
    monkeypatch.setenv("YURA_LARAVEL_TOKEN", token)
    assert la.configuracion() is None


def test_configuracion_valida(monkeypatch):
    monkeypatch.setenv("YURA_LARAVEL_SYNC_ENABLED", "1")
    monkeypatch.setenv("YURA_LARAVEL_URL", "https://demo.example/")
    monkeypatch.setenv("YURA_LARAVEL_TOKEN", "x")
    assert la.configuracion() == ("https://demo.example", "x")


def test_diccionario_explicito_y_por_defecto(monkeypatch, tmp_path):
    monkeypatch.delenv("YURA_DICTIONARY_PATH", raising=False)
    assert la.ruta_diccionario() == DICCIONARIO
    otro = tmp_path / "otro.db"
    otro.write_bytes(b"")
    monkeypatch.setenv("YURA_DICTIONARY_PATH", str(otro))
    assert la.ruta_diccionario() == str(otro)
    monkeypatch.setenv("YURA_DICTIONARY_PATH", str(tmp_path / "no_existe.db"))
    assert la.ruta_diccionario() == DICCIONARIO


# ------------------------------------------------------------ cliente HTTP

class Respuesta(io.BytesIO):
    def __init__(self, status, cuerpo=b""):
        super().__init__(cuerpo)
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def _abrir_falso(status, cuerpo=None, pedidos=None):
    def abrir(pedido, timeout):
        if pedidos is not None:
            pedidos.append(pedido)
        datos = json.dumps(cuerpo).encode() if cuerpo is not None else b""
        if status >= 400:
            raise urllib.error.HTTPError(pedido.full_url, status, "error", {}, io.BytesIO(datos))
        return Respuesta(status, datos)
    return abrir


def test_reclamar_cola_vacia_devuelve_none():
    cliente = la.ClienteLaravel("https://demo.example", "secreto", abrir=_abrir_falso(204))
    assert cliente.reclamar() is None


def test_reclamar_envia_el_token_en_la_cabecera():
    pedidos = []
    cuerpo = {"contract_version": "1.2", "activity": _actividad()}
    cliente = la.ClienteLaravel("https://demo.example", "secreto", abrir=_abrir_falso(200, cuerpo, pedidos))
    assert cliente.reclamar()["attempt_id"] == _actividad()["attempt_id"]
    assert pedidos[0].full_url == "https://demo.example/api/v1/robot/activities/next"
    assert pedidos[0].get_method() == "GET"
    assert pedidos[0].get_header("Authorization") == "Bearer secreto"


def test_reclamar_rechaza_otra_version_del_contrato():
    cuerpo = {"contract_version": "1.1", "activity": _actividad()}
    cliente = la.ClienteLaravel("https://demo.example", "x", abrir=_abrir_falso(200, cuerpo))
    with pytest.raises(la.ErrorLaravel):
        cliente.reclamar()


def test_estado_y_envio_usan_las_rutas_del_contrato():
    pedidos = []
    actividad = _actividad()
    cliente = la.ClienteLaravel("https://demo.example", "secreto",
                                abrir=_abrir_falso(200, {"status": "cancelled"}, pedidos))
    assert cliente.estado(actividad["activity_id"], actividad["attempt_id"]) == "cancelled"
    cliente.enviar({"activity_id": actividad["activity_id"], "attempt_id": actividad["attempt_id"]})
    assert pedidos[0].full_url.endswith(
        f"/api/v1/robot/activities/{actividad['activity_id']}/attempts/{actividad['attempt_id']}/status")
    assert pedidos[1].full_url.endswith(f"/api/v1/robot/activities/{actividad['activity_id']}/results")
    assert pedidos[1].get_method() == "POST"
    assert "secreto" not in pedidos[1].data.decode()


def test_red_caida_es_error_de_red():
    def abrir(pedido, timeout):
        raise urllib.error.URLError("sin conexión")
    cliente = la.ClienteLaravel("https://demo.example", "x", abrir=abrir)
    with pytest.raises(la.ErrorRed):
        cliente.reclamar()


# ------------------------------------------------------------ plan y nota

def test_plan_valido_y_respondiente_ajeno():
    assert la.problemas_del_plan(_actividad()) == []
    malo = _actividad(respondientes=(103, 999))
    assert la.problemas_del_plan(malo)


def test_vocabulario_de_categoria_del_diccionario():
    import sqlite3
    with sqlite3.connect(DICCIONARIO) as conexion:
        colores = la.vocabulario_de_categoria(conexion, "nivel1_colores")
        assert colores and all(espanol and quechua for espanol, quechua in colores)
        assert la.vocabulario_de_categoria(conexion, "nivel1_saludos")
        assert la.vocabulario_de_categoria(conexion, "drop table") == []


def test_planificar_respeta_respondientes_y_cantidad():
    actividad = _actividad(por_respondiente=2)
    actividad["groups"].append({
        "group_id": "g2", "members": [{"student_id": 201, "display_name": "Rosa"}],
        "respondent_student_ids": [201],
    })
    preguntas = la.planificar(actividad, [("rojo", "Puka"), ("azul", "Anqas")], random.Random(3))
    assert sorted(p["question_id"] for p in preguntas) == sorted([
        "group-1-103-1", "group-1-103-2", "group-1-101-1", "group-1-101-2", "group-2-201-1", "group-2-201-2"])
    assert {p["student_id"] for p in preguntas} == {103, 101, 201}


def test_nota_del_ejemplo_del_contrato():
    actividad = _actividad()
    respuestas = {"group-1-103-1": (True, "2026-10-06T17:03:12Z"), "group-1-101-1": (False, "2026-10-06T17:04:12Z")}
    grupo = la.calificar(actividad, respuestas)[0]
    assert grupo["member_student_ids"] == [101, 102, 103]
    assert grupo["respondent_student_ids"] == [103, 101]
    assert (grupo["points_earned"], grupo["points_possible"], grupo["score_percentage"]) == (50, 100, 50)
    assert grupo["responses"][0] == {
        "student_id": 103, "question_id": "group-1-103-1", "correct": True,
        "points_earned": 50, "points_possible": 50, "answered_at": "2026-10-06T17:03:12Z"}


def test_nota_con_tres_respuestas_sale_de_los_totales():
    actividad = _actividad(respondientes=(101, 102, 103))
    respuestas = {"group-1-101-1": (True, None), "group-1-102-1": (True, None), "group-1-103-1": (False, None)}
    grupo = la.calificar(actividad, respuestas)[0]
    assert (grupo["points_earned"], grupo["points_possible"], grupo["score_percentage"]) == (66.66, 99.99, 66.67)


# ------------------------------------------------------------ ejecución

def test_actividad_completa_califica_y_envia(tmp_path):
    cliente = ClienteFalso()
    ejecutor, dichas, mostradas = _ejecutor(tmp_path, cliente, [])
    actividad = _actividad()
    # Respuesta correcta para la primera pregunta; silencio en la segunda.
    plan = la.planificar(actividad, la.vocabulario_de_categoria(
        __import__("sqlite3").connect(DICCIONARIO), "nivel1_colores"), random.Random(1))
    oidas = iter([plan[0]["quechua"], "", ""])
    ejecutor.escuchar = lambda pistas: next(oidas, "")

    resumen = ejecutor.ejecutar(actividad)

    assert resumen["status"] == "completed"
    grupo = resumen["group_results"][0]
    assert grupo["score_percentage"] == 50
    assert [r["correct"] for r in grupo["responses"] if r["question_id"] == plan[0]["question_id"]] == [True]
    assert cliente.enviados == [resumen]
    assert os.listdir(tmp_path / "outbox" / "enviados")
    assert any("Ana" in nombre or "María" in nombre for nombre, _ in mostradas)
    assert all(pregunta.startswith("¿Cómo se dice ") and pregunta.endswith(" en quechua?") for _, pregunta in mostradas)


def test_cancelada_a_mitad_no_envia_notas(tmp_path):
    # in_progress al empezar y en la 1.ª pregunta; cancelled antes de la 2.ª.
    cliente = ClienteFalso(estados=["in_progress", "in_progress", "cancelled"])
    ejecutor, dichas, _ = _ejecutor(tmp_path, cliente, ["puka", "anqas"])
    assert ejecutor.ejecutar(_actividad()) is None
    assert cliente.enviados == []
    assert not os.listdir(tmp_path / "outbox" / "pendientes")


def test_intento_reemplazado_al_final_no_envia(tmp_path):
    cliente = ClienteFalso(estados=["in_progress", "in_progress", "in_progress", "superseded"])
    ejecutor, _, _ = _ejecutor(tmp_path, cliente, ["puka", "anqas"])
    assert ejecutor.ejecutar(_actividad()) is None
    assert cliente.enviados == []


def test_categoria_sin_vocabulario_falla_sin_notas(tmp_path):
    cliente = ClienteFalso()
    ejecutor, _, _ = _ejecutor(tmp_path, cliente, [])
    resumen = ejecutor.ejecutar(_actividad(categoria="nivel9_inventada"))
    assert resumen["status"] == "failed"
    assert "nivel9_inventada" in resumen["failure_reason"]
    assert "group_results" not in resumen


def test_error_durante_la_actividad_falla_sin_notas(tmp_path):
    cliente = ClienteFalso()
    ejecutor, _, _ = _ejecutor(tmp_path, cliente, [])

    def microfono_roto(pistas):
        raise OSError("micrófono desconectado")
    ejecutor.escuchar = microfono_roto
    resumen = ejecutor.ejecutar(_actividad())
    assert resumen["status"] == "failed" and "group_results" not in resumen


# ------------------------------------------------------------ outbox

@pytest.mark.parametrize("codigo, carpeta", [(201, "enviados"), (409, "revisar"), (422, "revisar"),
                                            (500, "pendientes"), ("red", "pendientes")])
def test_outbox_segun_la_respuesta_de_laravel(tmp_path, codigo, carpeta):
    outbox = la.Outbox(str(tmp_path / "outbox"))
    outbox.guardar(la.resumen_fallido(_actividad(), "prueba"))
    outbox.enviar_pendientes(ClienteFalso(codigo_envio=codigo))
    assert [n for n in os.listdir(tmp_path / "outbox" / carpeta) if n.endswith(".json")]
