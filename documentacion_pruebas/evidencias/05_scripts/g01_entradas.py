"""Grupo 1: entradas extremas a conversacion, traductor, juego y BrainYura."""
from comun import *  # noqa
from unittest.mock import Mock
import conversacion
import traductor
from juego import Juego
from main_robot import BrainYura, RobotStates

conn = conexion_copia("g01.db")
conversacion._conexion_vocabulario = conn  # evita abrir la BD real

ENTRADAS = [
    ("vacio", ""),
    ("espacios", "     "),
    ("None", None),
    ("5000c", "hola " * 1000),
    ("100000c", "a" * 100000),
    ("emojis", "😀🦙🔥"),
    ("sql", "' \" ; -- DROP TABLE nivel1_familia;"),
    ("porcentaje", "%"),
    ("guion_bajo", "_"),
    ("nulo", "\x00"),
    ("saltos", "hola\n\n\ncomo\r\nestas"),
    ("ingles", "how do you say water in quechua"),
    ("num_123", "123"),
    ("num_-5", "-5"),
    ("mezcla", "rimaykullayki como estas yura"),
    ("repetidas", "jugar jugar jugar"),
    ("jugar_y_salir", "jugar y salir"),
    ("traducir_apagar", "traducir apagar"),
    ("menudo", "menudo"),
    ("salirse", "salirse"),
    ("conjugar", "conjugar"),
    ("nomas", "nomás"),
    ("apagarlo", "apagarlo"),
    ("noche", "noche"),
]

n = [0]
e_nombre = [""]
e_metodo = [""]
# Veredicto manual tras revisar la salida (FALLA = comportamiento incorrecto aunque no haya excepción)
VEREDICTO = {
    ("conversacion", "menudo"): "FALLA",       # 'menudo' contiene 'menu' -> sale
    ("conversacion", "conjugar"): "FALLA",     # 'conjugar' contiene 'jugar' -> inicia práctica
    ("conversacion", "noche"): "OBSERVACION",  # palabra válida rechazada como fuera de tema
    ("conversacion", "nomas"): "OBSERVACION",
    ("conversacion", "salirse"): "OBSERVACION",
    ("traductor", "5000c"): "OBSERVACION",     # texto completo enviado a Groq
    ("traductor", "100000c"): "FALLA",         # 100.000 caracteres enviados a Groq sin límite
    ("traductor", "menudo"): "FALLA",
    ("traductor", "salirse"): "OBSERVACION",
    ("traductor", "apagarlo"): "OBSERVACION",
    ("traductor", "traducir_apagar"): "OBSERVACION",
    ("juego", "menudo"): "FALLA",
    ("juego", "salirse"): "OBSERVACION",
    ("juego", "vacio"): "OBSERVACION",         # no avanza: se repite la misma pregunta
    ("ejecutar_menu", "menudo"): "FALLA",      # se despide y sigue en MENU
    ("ejecutar_menu", "conjugar"): "FALLA",    # entra al JUEGO
    ("ejecutar_menu", "traducir_apagar"): "OBSERVACION",  # apaga el robot
    ("ejecutar_menu", "apagarlo"): "OBSERVACION",
    ("ejecutar_menu", "noche"): "OBSERVACION",
    ("ejecutar_menu", "salirse"): "OBSERVACION",
    ("ejecutar_conversar", "menudo"): "FALLA",
    ("ejecutar_conversar", "conjugar"): "FALLA",
    ("ejecutar_conversar", "noche"): "OBSERVACION",
    ("ejecutar_conversar", "espacios"): "OBSERVACION",  # dice 'No logré escucharte' pero con '' calla
}


def nid():
    n[0] += 1
    return f"YURA-EXT-{n[0]:03d}"


# ------------------------------------------------------------ conversacion.procesar_entrada
print("\n########## conversacion.procesar_entrada ##########")
for nombre, entrada in ENTRADAS:
    e_nombre[0] = nombre
    conversacion.cancelar_sesion_educativa()
    groq = groq_que_devuelve("RESPUESTA_GROQ_FALSA")
    hist = []

    def fn(e=entrada, g=groq, h=hist):
        return conversacion.procesar_entrada(e, g, h)

    def ev(r, g=groq, e=entrada):
        if isinstance(r, BaseException):
            return "ERROR", f"excepción {type(r).__name__}"
        estado = VEREDICTO.get(("conversacion", e_nombre[0]), "OK")
        env = ""
        if g.llamadas:
            user = g.llamadas[-1]["messages"][-1]["content"]
            sysm = g.llamadas[-1]["messages"][0]["content"]
            env = f" | Groq llamado: user={len(user)} car, system={len(sysm)} car"
        return estado, f"accion={r['accion']} resp={r['respuesta'][:90]!r}{env}"
    caso(nid(), "conversacion", "procesar_entrada", nombre, "sin excepción, respuesta razonable", fn, ev)

# ------------------------------------------------------------ traductor.ejecutar_traducir
print("\n########## traductor.ejecutar_traducir (1 iteración) ##########")
for nombre, entrada in ENTRADAS:
    e_nombre[0] = nombre
    habla = []
    vueltas = [0]

    def activo(v=vueltas):
        v[0] += 1
        return v[0] <= 1

    groq = groq_que_devuelve("NO_ENCONTRADO")

    def fn(e=entrada, h=habla, a=activo, g=groq):
        return traductor.ejecutar_traducir(lambda: e, h.append, conn, g, a)

    def ev(r, h=habla, g=groq):
        if isinstance(r, BaseException):
            return "ERROR", f"excepción {type(r).__name__}"
        extra = f" | Groq user={len(g.llamadas[-1]['messages'][-1]['content'])} car" if g.llamadas else ""
        return VEREDICTO.get(("traductor", e_nombre[0]), "OK"), f"ret={r} habló={[x[:70] for x in h]}{extra}"
    caso(nid(), "traductor", "ejecutar_traducir", nombre, "sin excepción; salir solo con orden clara", fn, ev)

# ------------------------------------------------------------ Juego.ejecutar_turno
print("\n########## Juego.ejecutar_turno ##########")
for nombre, entrada in ENTRADAS:
    e_nombre[0] = nombre
    habla = []
    j = Juego(["gato", "perro", "sol", "agua", "casa", "arbol"],
              lambda p: traductor.consultar_diccionario_local(p, conn),
              lambda e=entrada: e, habla.append, lambda c: None,
              BrainYura._normalizar_texto.__get__(object.__new__(BrainYura)))

    def fn(j=j):
        return j.ejecutar_turno()

    def ev(r, h=habla, j=j):
        if isinstance(r, BaseException):
            return "ERROR", f"excepción {type(r).__name__}"
        return VEREDICTO.get(("juego", e_nombre[0]), "OK"), f"ret={r} indice={j.indice_juego} habló={[x[:60] for x in h]}"
    caso(nid(), "juego", "ejecutar_turno", nombre, "sin excepción; salir solo con orden clara", fn, ev)


# ------------------------------------------------------------ BrainYura
def robot_falso(entrada, estado=RobotStates.MENU):
    r = object.__new__(BrainYura)
    r.state = estado
    r.running = True
    r.saludo_inicial_done = True
    r.hw = Mock()
    r.escuchar_voz = Mock(return_value=entrada)
    r._set_web_status = Mock()
    r.groq_client = groq_que_devuelve("RESPUESTA_GROQ_FALSA")
    r.historial_conversacion = []
    r.juego = Mock()
    r.db_conn = conn
    return r


for metodo, estado in (("ejecutar_menu", RobotStates.MENU),
                       ("ejecutar_conversar", RobotStates.CONVERSAR),
                       ("ejecutar_silencio", RobotStates.SILENCIO)):
    print(f"\n########## BrainYura.{metodo} ##########")
    for nombre, entrada in ENTRADAS:
        e_nombre[0] = nombre
        e_metodo[0] = metodo
        conversacion.cancelar_sesion_educativa()
        r = robot_falso(entrada, estado)

        def fn(r=r, m=metodo):
            return getattr(r, m)()

        def ev(res, r=r):
            if isinstance(res, BaseException):
                return "ERROR", f"excepción {type(res).__name__}"
            h = [c.args[0][:60] for c in r.hw.hablar.call_args_list]
            return VEREDICTO.get((e_metodo[0], e_nombre[0]), "OK"), f"estado={r.state} running={r.running} habló={h}"
        caso(nid(), "main_robot", metodo, nombre, "sin excepción; estado coherente", fn, ev)


# ------------------------------------------------------------ casos complementarios de colisión de comandos
print("\n########## Colisiones de palabras clave ##########")
n[0] = 150
COMPLEMENTARIOS = [
    ("ejecutar_menu", "no quiero apagar", "NO debe apagar"),
    ("ejecutar_menu", "no te vayas a apagar yura", "NO debe apagar"),
    ("ejecutar_menu", "como se dice apagar la luz", "NO debe apagar"),
    ("ejecutar_menu", "como se dice adios en quechua", "traducir adiós, no despedirse"),
    ("ejecutar_conversar", "como se dice adios en quechua", "traducir adiós"),
    ("ejecutar_conversar", "como se dice menu en quechua", "responder, no volver al menú"),
    ("ejecutar_silencio", "guarda silencio", "seguir en SILENCIO"),
    ("ejecutar_silencio", "no vuelvas todavia", "seguir en SILENCIO"),
    ("ejecutar_menu", "silencio no quiero jugar", "SILENCIO (ambiguo)"),
]
for metodo, frase, esperado in COMPLEMENTARIOS:
    estado_ini = {"ejecutar_menu": RobotStates.MENU, "ejecutar_conversar": RobotStates.CONVERSAR,
                  "ejecutar_silencio": RobotStates.SILENCIO}[metodo]
    conversacion.cancelar_sesion_educativa()
    r = robot_falso(frase, estado_ini)

    def fn(r=r, m=metodo):
        return getattr(r, m)()

    def ev(res, r=r, esp=esperado, ini=estado_ini):
        h = [c.args[0][:70] for c in r.hw.hablar.call_args_list]
        malo = False
        if "NO debe apagar" in esp and (r.state == RobotStates.SALIR or not r.running):
            malo = True
        if "adiós" in esp and any("Hasta luego" in x for x in h):
            malo = True
        if "no volver al menú" in esp and r.state == RobotStates.MENU:
            malo = True
        if esp == "seguir en SILENCIO" and r.state != RobotStates.SILENCIO:
            malo = True
        return ("FALLA" if malo else "OK"), f"estado={r.state} running={r.running} habló={h}"
    caso(nid(), "main_robot", metodo, repr(frase), esperado, fn, ev)

# traductor: pedir traducir palabras que son comandos de salida
for frase in ("adios", "volver", "devolver", "terminar", "menu del dia"):
    habla = []
    v = [0]

    def fn(f=frase, h=habla, v=v):
        return traductor.ejecutar_traducir(lambda: f, h.append, conn, None,
                                           lambda: (v.__setitem__(0, v[0] + 1) or v[0] <= 1))

    def ev(res, h=habla):
        return ("FALLA" if res == "menu" else "OK"), f"ret={res} habló={h}"
    caso(nid(), "traductor", "ejecutar_traducir", repr(frase), "traducir la palabra (no salir)", fn, ev)

resumen()
volcar_matriz("../05_g01_matriz.md")
