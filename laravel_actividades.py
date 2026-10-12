"""Actividades de clase enviadas por Laravel (Yura Activity Contract v1.2).

Laravel decide grupos, integrantes y respondientes; Yura reclama la
actividad, hace las preguntas con su diccionario local («¿Cómo se dice X en
quechua?»), escucha, califica y envía un resumen por grupo. Contrato:
documentacion_pruebas/yura-activity-contract-v1.md.

Configuración (.env.local):
    YURA_LARAVEL_URL=https://...        raíz de Laravel, sin /api al final
    YURA_LARAVEL_TOKEN=...              token Sanctum de la cuenta robot
    YURA_LARAVEL_SYNC_ENABLED=1         0 (por defecto): no consulta nada
    YURA_LARAVEL_INTERVALO=15           segundos entre consultas (por defecto 15)
    YURA_DICTIONARY_PATH=/ruta/diccionario.db   (opcional)

Decisiones donde el contrato no es explícito (ver el informe del 12/10/2026):
- Cada respuesta planificada vale round(100 / respuestas del grupo, 2); los
  totales del grupo son la suma y el porcentaje sale de los totales.
- Nunca se envía "partial": si algo falla a mitad, se envía "failed" sin
  notas, para que el docente pueda reintentar con el mismo plan.
- Sin respuesta, se repite la pregunta una vez; si sigue el silencio, cuenta
  como incorrecta (cero puntos).
"""
import ipaddress
import json
import os
import random
import re
import sqlite3
import urllib.error
import urllib.request
from datetime import datetime, timezone
from urllib.parse import quote, urlparse

import depuracion
import pronunciaciones
import texto as texto_util
import traductor

RAIZ = os.path.dirname(os.path.abspath(__file__))
VERSION_CONTRATO = "1.2"
DICCIONARIO_DEL_CONTRATO = "diccionario_quechua_sqlite_29-07-2026.db"
CARPETA_OUTBOX = os.path.join(RAIZ, "basedatos", "outbox_laravel")
ESTADOS_DE_PARADA = {"cancelled", "superseded"}
# Categorías que la web puede pedir (tablas del diccionario).
CATEGORIAS = {
    "nivel1_alimentos": "los alimentos",
    "nivel1_colores": "los colores",
    "nivel1_elementos_casa": "las cosas de la casa",
    "nivel1_elementos_naturales": "la naturaleza",
    "nivel1_familia": "la familia",
    "nivel1_numeros": "los números",
    "nivel1_objetos_escolares": "los objetos de la escuela",
    "nivel1_partes_del_cuerpo": "las partes del cuerpo",
    "nivel1_saludos": "los saludos",
    "nivel2_animales": "los animales",
}


class ErrorLaravel(Exception):
    """Laravel respondió algo que el contrato no espera."""

    def __init__(self, mensaje, codigo=None):
        super().__init__(mensaje)
        self.codigo = codigo


class ErrorRed(Exception):
    """No se pudo hablar con Laravel (red caída, tiempo agotado)."""


def ahora():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ------------------------------------------------------------ configuración

def ruta_diccionario():
    """El diccionario de las actividades: YURA_DICTIONARY_PATH si existe;
    si no, el archivo del contrato en la raíz; si no, diccionario.db."""
    explicita = os.environ.get("YURA_DICTIONARY_PATH", "").strip()
    if explicita and os.path.isfile(explicita):
        return explicita
    del_contrato = os.path.join(RAIZ, DICCIONARIO_DEL_CONTRATO)
    if os.path.isfile(del_contrato):
        return del_contrato
    return os.path.join(RAIZ, "diccionario.db")


def url_permitida(url):
    """HTTPS siempre; HTTP solo en una red privada (desarrollo)."""
    partes = urlparse(url or "")
    if partes.scheme == "https" and partes.hostname:
        return True
    if partes.scheme != "http" or not partes.hostname:
        return False
    if partes.hostname == "localhost" or partes.hostname.endswith(".local"):
        return True
    try:
        direccion = ipaddress.ip_address(partes.hostname)
    except ValueError:
        return False
    return direccion.is_private or direccion.is_loopback


def configuracion():
    """(url, token) si la sincronización está activa y bien configurada."""
    if os.environ.get("YURA_LARAVEL_SYNC_ENABLED", "0").strip() != "1":
        return None
    url = os.environ.get("YURA_LARAVEL_URL", "").strip().rstrip("/")
    token = os.environ.get("YURA_LARAVEL_TOKEN", "").strip()
    if not url or not token:
        print("[LARAVEL] Sincronización activada pero faltan YURA_LARAVEL_URL o YURA_LARAVEL_TOKEN.")
        return None
    if url.endswith("/api"):
        print("[LARAVEL] YURA_LARAVEL_URL debe ser la raíz, sin /api al final.")
        return None
    if not url_permitida(url):
        print("[LARAVEL] YURA_LARAVEL_URL debe usar HTTPS (HTTP solo en una red privada).")
        return None
    return url, token


def intervalo_consultas():
    try:
        return max(5.0, float(os.environ.get("YURA_LARAVEL_INTERVALO", "15")))
    except ValueError:
        return 15.0


# ------------------------------------------------------------ cliente HTTP

class ClienteLaravel:
    """Las tres rutas del contrato. El token va en la cabecera, nunca en el JSON."""

    def __init__(self, url, token, tiempo=10, abrir=None):
        self.url = url.rstrip("/")
        self._token = token
        self.tiempo = tiempo
        self._abrir = abrir or urllib.request.urlopen

    def _pedir(self, metodo, ruta, cuerpo=None):
        datos = None if cuerpo is None else json.dumps(cuerpo, ensure_ascii=False).encode("utf-8")
        cabeceras = {"Accept": "application/json", "Authorization": f"Bearer {self._token}"}
        if datos is not None:
            cabeceras["Content-Type"] = "application/json"
        pedido = urllib.request.Request(self.url + ruta, data=datos, method=metodo, headers=cabeceras)
        try:
            with self._abrir(pedido, timeout=self.tiempo) as respuesta:
                codigo, texto = respuesta.status, respuesta.read()
        except urllib.error.HTTPError as error:
            codigo, texto = error.code, error.read()
        except (urllib.error.URLError, OSError) as error:
            raise ErrorRed(str(error)) from error
        try:
            contenido = json.loads(texto) if texto else None
        except ValueError:
            contenido = None
        return codigo, contenido

    def reclamar(self):
        """La actividad pendiente más antigua (la marca in_progress), o None."""
        codigo, datos = self._pedir("GET", "/api/v1/robot/activities/next")
        if codigo == 204:
            return None
        if codigo != 200 or not isinstance(datos, dict):
            raise ErrorLaravel(f"Respuesta inesperada al reclamar ({codigo}).", codigo)
        if str(datos.get("contract_version")) != VERSION_CONTRATO:
            raise ErrorLaravel(f"Versión de contrato distinta: {datos.get('contract_version')}.", codigo)
        actividad = datos.get("activity")
        if not isinstance(actividad, dict):
            raise ErrorLaravel("La respuesta no trae la actividad.", codigo)
        return actividad

    def estado(self, activity_id, attempt_id):
        ruta = (f"/api/v1/robot/activities/{quote(str(activity_id), safe='')}"
                f"/attempts/{quote(str(attempt_id), safe='')}/status")
        codigo, datos = self._pedir("GET", ruta)
        if codigo != 200 or not isinstance(datos, dict):
            raise ErrorLaravel(f"Respuesta inesperada al consultar el estado ({codigo}).", codigo)
        return str(datos.get("status", ""))

    def enviar(self, resumen):
        """Código HTTP de Laravel al recibir el resumen."""
        ruta = f"/api/v1/robot/activities/{quote(str(resumen['activity_id']), safe='')}/results"
        codigo, _ = self._pedir("POST", ruta, resumen)
        return codigo


# ------------------------------------------------------------ outbox

class Outbox:
    """Cada resumen se guarda en disco antes de enviarlo.

    pendientes/: aún no llegó (red o servidor caídos): se reintenta.
    enviados/:   Laravel lo aceptó.
    revisar/:    Laravel lo rechazó (409, 422, 401, 403...): queda para revisión.
    Nunca se borra nada.
    """

    def __init__(self, carpeta=CARPETA_OUTBOX):
        self.carpeta = carpeta
        for sub in ("pendientes", "enviados", "revisar"):
            os.makedirs(os.path.join(carpeta, sub), exist_ok=True)

    @staticmethod
    def _nombre(resumen):
        limpio = lambda valor: re.sub(r"[^A-Za-z0-9-]", "_", str(valor))[:80]
        return f"{limpio(resumen['activity_id'])}__{limpio(resumen['attempt_id'])}.json"

    def guardar(self, resumen):
        ruta = os.path.join(self.carpeta, "pendientes", self._nombre(resumen))
        temporal = ruta + ".tmp"
        with open(temporal, "w", encoding="utf-8") as archivo:
            json.dump(resumen, archivo, ensure_ascii=False, indent=2)
        os.replace(temporal, ruta)
        return ruta

    def pendientes(self):
        carpeta = os.path.join(self.carpeta, "pendientes")
        return sorted(os.path.join(carpeta, n) for n in os.listdir(carpeta) if n.endswith(".json"))

    def enviar_pendientes(self, cliente):
        """Intenta enviar todo lo pendiente. Devuelve {nombre: código o 'red'}."""
        resultado = {}
        for ruta in self.pendientes():
            nombre = os.path.basename(ruta)
            with open(ruta, encoding="utf-8") as archivo:
                resumen = json.load(archivo)
            try:
                codigo = cliente.enviar(resumen)
            except ErrorRed:
                resultado[nombre] = "red"
                continue
            resultado[nombre] = codigo
            if 200 <= codigo < 300:
                os.replace(ruta, os.path.join(self.carpeta, "enviados", nombre))
            elif 400 <= codigo < 500:
                destino = os.path.join(self.carpeta, "revisar", nombre)
                os.replace(ruta, destino)
                with open(destino + ".codigo", "w", encoding="utf-8") as archivo:
                    archivo.write(f"{codigo} {ahora()}\n")
            # 5xx: queda en pendientes para el próximo intento.
        return resultado


# ------------------------------------------------------------ plan

def problemas_del_plan(actividad):
    """Lo que impide ejecutar la actividad tal como vino ([] si nada)."""
    problemas = []
    for clave in ("activity_id", "attempt_id", "content", "groups", "execution"):
        if not actividad.get(clave):
            problemas.append(f"Falta {clave}.")
    if problemas:
        return problemas
    try:
        por_respondiente = int(actividad["execution"].get("questions_per_respondent", 0))
    except (TypeError, ValueError):
        por_respondiente = 0
    if por_respondiente < 1:
        problemas.append("questions_per_respondent debe ser 1 o más.")
    vistos = set()
    for grupo in actividad["groups"]:
        integrantes = {m.get("student_id") for m in grupo.get("members", [])}
        respondientes = grupo.get("respondent_student_ids") or []
        if not grupo.get("group_id"):
            problemas.append("Un grupo no tiene group_id.")
        if not respondientes:
            problemas.append(f"El grupo {grupo.get('group_id')} no tiene respondientes.")
        if not set(respondientes) <= integrantes:
            problemas.append(f"El grupo {grupo.get('group_id')} tiene respondientes que no son integrantes.")
        if len(set(respondientes)) != len(respondientes):
            problemas.append(f"El grupo {grupo.get('group_id')} repite respondientes.")
        if grupo.get("group_id") in vistos:
            problemas.append(f"El grupo {grupo.get('group_id')} aparece dos veces.")
        vistos.add(grupo.get("group_id"))
    return problemas


def vocabulario_de_categoria(conexion, categoria):
    """[(castellano, quechua)] que se pueden preguntar en esta categoría:
    una sola traducción, distinta en los dos idiomas, palabra simple."""
    if categoria not in CATEGORIAS or conexion is None:
        return []
    try:
        registros = traductor._leer_registros_vocabulario(conexion)
    except sqlite3.Error:
        return []
    usables = []
    for registro in registros:
        if registro["tabla_origen"] != categoria:
            continue
        espanol = str(registro["espanol"] or "").strip()
        quechua = str(registro["quechua"] or "").strip()
        if not espanol or not quechua:
            continue
        if categoria == "nivel1_numeros" and registro["id"] > 10:
            continue
        if any(signo in espanol for signo in "/()") or len(espanol.split()) > 3:
            continue
        if traductor._normalizar_para_comparar(espanol) == traductor._normalizar_para_comparar(quechua):
            continue
        if len(traductor.buscar_vocabulario(espanol, "espanol", conexion)["resultados"]) != 1:
            continue
        usables.append((espanol.lower(), quechua))
    return sorted(set(usables))


def planificar(actividad, vocabulario, azar):
    """Las preguntas en el orden en que se harán (mezcladas entre grupos)."""
    por_respondiente = int(actividad["execution"]["questions_per_respondent"])
    preguntas = []
    for indice, grupo in enumerate(actividad["groups"], 1):
        nombres = {m["student_id"]: str(m.get("display_name") or "").strip() for m in grupo["members"]}
        for student_id in grupo["respondent_student_ids"]:
            for numero in range(1, por_respondiente + 1):
                preguntas.append({
                    "group_id": grupo["group_id"],
                    "student_id": student_id,
                    "display_name": nombres.get(student_id) or "",
                    "question_id": f"group-{indice}-{student_id}-{numero}",
                })
    azar.shuffle(preguntas)
    palabras = []
    for pregunta in preguntas:
        if not palabras:  # se repite el vocabulario solo si se acabó
            palabras = list(vocabulario)
            azar.shuffle(palabras)
        pregunta["espanol"], pregunta["quechua"] = palabras.pop()
    return preguntas


def calificar(actividad, respuestas):
    """group_results del contrato. respuestas: {question_id: (correcta, answered_at)}."""
    por_respondiente = int(actividad["execution"]["questions_per_respondent"])
    resultados = []
    for indice, grupo in enumerate(actividad["groups"], 1):
        respondientes = list(grupo["respondent_student_ids"])
        planificadas = len(respondientes) * por_respondiente
        peso = round(100 / planificadas, 2)
        detalle = []
        for student_id in respondientes:
            for numero in range(1, por_respondiente + 1):
                question_id = f"group-{indice}-{student_id}-{numero}"
                correcta, answered_at = respuestas.get(question_id, (False, None))
                detalle.append({
                    "student_id": student_id,
                    "question_id": question_id,
                    "correct": bool(correcta),
                    "points_earned": peso if correcta else 0,
                    "points_possible": peso,
                    "answered_at": answered_at or ahora(),
                })
        ganados = round(sum(r["points_earned"] for r in detalle), 2)
        posibles = round(sum(r["points_possible"] for r in detalle), 2)
        resultados.append({
            "group_id": grupo["group_id"],
            "member_student_ids": [m["student_id"] for m in grupo["members"]],
            "respondent_student_ids": respondientes,
            "points_earned": ganados,
            "points_possible": posibles,
            "score_percentage": round(ganados / posibles * 100, 2) if posibles else 0,
            "responses": detalle,
        })
    return resultados


def resumen_fallido(actividad, motivo, started_at=None):
    return {
        "contract_version": VERSION_CONTRATO,
        "activity_id": actividad.get("activity_id"),
        "attempt_id": actividad.get("attempt_id"),
        "status": "failed",
        "started_at": started_at or ahora(),
        "finished_at": ahora(),
        "failure_reason": motivo,
    }


# ------------------------------------------------------------ ejecución

class ActividadDetenida(Exception):
    """Laravel canceló el intento o ya no es el actual: no se envía nada."""


class EjecutorActividad:
    """Ejecuta una actividad con la voz y la escucha de Yura.

    hablar(texto), escuchar(pistas) -> texto oído, mostrar(nombre, pregunta).
    """

    def __init__(self, cliente, outbox, hablar, escuchar, mostrar=None, ruta_db=None, azar=None):
        self.cliente = cliente
        self.outbox = outbox
        self.hablar = hablar
        self.escuchar = escuchar
        self.mostrar = mostrar or (lambda nombre, pregunta: None)
        self.ruta_db = ruta_db or ruta_diccionario()
        self.azar = azar or random.Random()

    def _revisar_estado(self, actividad):
        try:
            estado = self.cliente.estado(actividad["activity_id"], actividad["attempt_id"])
        except ErrorRed:
            return  # sin red no se sabe; se sigue y se vuelve a preguntar
        if estado in ESTADOS_DE_PARADA:
            raise ActividadDetenida(estado)

    def _preguntar(self, pregunta, pistas):
        frase = f"¿Cómo se dice {pregunta['espanol']} en quechua?"
        self.mostrar(pregunta["display_name"], frase)
        nombre = pregunta["display_name"]
        self.hablar(f"{nombre}, ¿cómo se dice {pregunta['espanol']} en quechua?" if nombre else frase)
        oido = self.escuchar(pistas)
        if not oido:
            self.hablar(f"No te escuché. Otra vez: {frase}")
            oido = self.escuchar(pistas)
        correcta = bool(oido) and pronunciaciones.respuesta_aceptada(oido, pregunta["quechua"])
        depuracion.depurar(f"[LARAVEL] {pregunta['question_id']}: oído «{oido}» -> {correcta}")
        if correcta:
            self.hablar("¡Muy bien! Allinmi.")
        else:
            self.hablar(f"Se dice {pregunta['quechua']}.")
        return correcta, ahora()

    def ejecutar(self, actividad):
        """Ejecuta y entrega la actividad. Devuelve el resumen enviado al
        outbox, o None si Laravel la detuvo."""
        started_at = ahora()
        problemas = problemas_del_plan(actividad)
        if problemas:
            return self._entregar(resumen_fallido(actividad, "Plan inválido: " + " ".join(problemas), started_at))
        categoria = str((actividad.get("content") or {}).get("category", ""))
        with sqlite3.connect(self.ruta_db) as conexion:
            vocabulario = vocabulario_de_categoria(conexion, categoria)
        if not vocabulario:
            return self._entregar(resumen_fallido(
                actividad, f"La categoría {categoria} no tiene vocabulario utilizable en el diccionario local.",
                started_at))
        preguntas = planificar(actividad, vocabulario, self.azar)
        quechuas = sorted({q for _, q in vocabulario})
        print(f"[LARAVEL] Actividad: {len(actividad['groups'])} grupos, {len(preguntas)} preguntas, {categoria}.")
        respuestas = {}
        try:
            self._revisar_estado(actividad)
            self.hablar(f"Empezamos la actividad de {CATEGORIAS[categoria]}. Responde cuando escuches tu nombre.")
            for pregunta in preguntas:
                self._revisar_estado(actividad)
                otras = self.azar.sample(quechuas, min(6, len(quechuas)))
                pistas = list(dict.fromkeys([pregunta["quechua"]] + otras))
                self.azar.shuffle(pistas)
                respuestas[pregunta["question_id"]] = self._preguntar(pregunta, pistas)
            self._revisar_estado(actividad)
        except ActividadDetenida as parada:
            print(f"[LARAVEL] Actividad detenida por Laravel ({parada}); no se envían notas.")
            self.hablar("La actividad fue detenida por la profesora. Regresamos al menú.")
            return None
        except Exception as exc:
            print(f"[LARAVEL] Error durante la actividad: {type(exc).__name__}.")
            return self._entregar(resumen_fallido(
                actividad, f"Error en el cerebro durante la actividad: {type(exc).__name__}.", started_at))
        self.hablar("Terminamos la actividad. ¡Gracias a todos!")
        return self._entregar({
            "contract_version": VERSION_CONTRATO,
            "activity_id": actividad["activity_id"],
            "attempt_id": actividad["attempt_id"],
            "status": "completed",
            "started_at": started_at,
            "finished_at": ahora(),
            "group_results": calificar(actividad, respuestas),
        })

    def _entregar(self, resumen):
        self.outbox.guardar(resumen)
        enviados = self.outbox.enviar_pendientes(self.cliente)
        print(f"[LARAVEL] Resultado {resumen['status']}: {enviados}")
        return resumen
