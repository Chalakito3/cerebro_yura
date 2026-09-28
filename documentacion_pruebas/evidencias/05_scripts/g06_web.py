"""Grupo 6: web Flask con test_client (sin abrir puertos, sin robot real)."""
from comun import *  # noqa
import json
import time
import threading
from types import SimpleNamespace
import web.app as webapp
from main_robot import BrainYura, RobotStates

cli = webapp.app.test_client()
webapp.app.config["PROPAGATE_EXCEPTIONS"] = False  # comportamiento de producción


def robot_con_estado(**web_status):
    r = object.__new__(BrainYura)
    r.state = RobotStates.MENU
    r.running = True
    r.web_status = {"phase": "ESPERANDO", "content": "", "translation": "", "result": None, "updated_at": None}
    r.web_status.update(web_status)
    r.web_status_lock = threading.Lock()
    return r


webapp.robot = None
caso("YURA-EXT-601", "web", "/api/status con robot None", "GET", "200 BACKEND_NOT_STARTED",
     lambda: cli.get("/api/status"),
     lambda x: ("OK" if x.status_code == 200 and x.json["state"] == "BACKEND_NOT_STARTED" else "FALLA",
                f"{x.status_code} {x.json['state']}"))


class RobotRoto:
    state = RobotStates.MENU
    running = True

    def get_web_status(self):
        raise RuntimeError("fallo interno simulado")


webapp.robot = RobotRoto()
caso("YURA-EXT-602", "web", "/api/status con get_web_status que lanza excepción", "GET",
     "JSON de error controlado (p. ej. 503) que app.js pueda mostrar", lambda: cli.get("/api/status"),
     lambda x: ("FALLA" if x.status_code == 500 else "OK",
                f"{x.status_code} content-type={x.content_type} cuerpo={x.data[:80]!r}"))

webapp.robot = SimpleNamespace(state="ESTADO_INVENTADO", running=True, get_web_status=lambda: {})
caso("YURA-EXT-603", "web", "/api/status con estado desconocido y web_status vacío", "GET",
     "200 con valores por defecto", lambda: cli.get("/api/status"),
     lambda x: ("OK" if x.status_code == 200 else "FALLA", f"{x.status_code} {x.json}"))

webapp.robot = SimpleNamespace(state=RobotStates.MENU, get_web_status=lambda: {})
caso("YURA-EXT-604", "web", "/api/status con robot sin atributo running", "GET", "200 o error controlado",
     lambda: cli.get("/api/status"), lambda x: ("FALLA" if x.status_code == 500 else "OK", f"{x.status_code}"))

xss = "<script>alert('x')</script><img src=x onerror=alert(1)>"
webapp.robot = robot_con_estado(content=xss, translation=xss)
caso("YURA-EXT-605", "web", "/api/status con HTML/<script> en content", xss,
     "JSON válido; la página lo pinta como texto (textContent)", lambda: cli.get("/api/status"),
     lambda x: ("OK" if x.json["content"] == xss else "FALLA",
                f"{x.status_code}; JSON devuelve el texto tal cual; app.js usa textContent (líneas 175-182) -> no se ejecuta"))

grande = "Ñ" * (1024 * 1024)
webapp.robot = robot_con_estado(content=grande)
t0 = time.perf_counter()
resp = cli.get("/api/status")
dt = time.perf_counter() - t0
caso("YURA-EXT-606", "web", "/api/status con content de 1 MB", "1.048.576 caracteres 'Ñ'",
     "limitar tamaño", lambda: (resp.status_code, len(resp.data), dt),
     lambda x: ("OBSERVACION", f"{x[0]} respuesta={x[1]} bytes en {x[2]*1000:.0f} ms (sin límite de tamaño)"))

webapp.robot = None
for i, (metodo, ruta) in enumerate([("get", "/no-existe"), ("get", "/api/status/../../etc/passwd"),
                                     ("post", "/api/status"), ("delete", "/api/card"), ("put", "/")]):
    caso(f"YURA-EXT-6{10 + i:02d}", "web", f"{metodo.upper()} {ruta}", ruta,
         "404/405 sin filtrar información", lambda m=metodo, r=ruta: getattr(cli, m)(r),
         lambda x: ("OK" if x.status_code in (404, 405) and b"Traceback" not in x.data else "FALLA",
                    f"{x.status_code}"))

webapp.robot = robot_con_estado(content="Wasi")
t0 = time.perf_counter()
codigos = set()
for _ in range(1000):
    codigos.add(cli.get("/api/status").status_code)
dt = time.perf_counter() - t0
caso("YURA-EXT-620", "web", "1.000 peticiones seguidas a /api/status", "1000 x GET",
     "todas 200; sin límite de frecuencia es observación", lambda: (codigos, dt),
     lambda x: ("OK" if x[0] == {200} else "FALLA", f"códigos={x[0]} total={x[1]:.2f}s ({x[1]:.4f} ms por petición)"))

# 1000 peticiones concurrentes (hilos) mientras el robot escribe estado
errores = []


def lector():
    c = webapp.app.test_client()
    for _ in range(100):
        try:
            if c.get("/api/status").status_code != 200:
                errores.append("no200")
        except Exception as e:
            errores.append(repr(e))


def escritor(r):
    for i in range(2000):
        r._set_web_status("HABLANDO", content=f"c{i}", translation=f"t{i}")


r = webapp.robot
hilos = [threading.Thread(target=lector) for _ in range(10)] + [threading.Thread(target=escritor, args=(r,))]
t0 = time.perf_counter()
[h.start() for h in hilos]
[h.join() for h in hilos]
caso("YURA-EXT-621", "web", "1.000 peticiones en 10 hilos + escritor concurrente", "10x100 GET + 2000 _set_web_status",
     "sin errores", lambda: (errores, time.perf_counter() - t0),
     lambda x: ("OK" if not x[0] else "FALLA", f"errores={len(x[0])} tiempo={x[1]:.2f}s"))

resp = cli.get("/")
cab = {k.lower(): v for k, v in resp.headers.items()}
faltan = [h for h in ("content-security-policy", "x-content-type-options", "x-frame-options", "referrer-policy")
          if h not in cab]
caso("YURA-EXT-630", "web", "Cabeceras de seguridad en GET /", "GET /", "CSP, nosniff, X-Frame-Options, Referrer-Policy",
     lambda: (resp.status_code, faltan, cab.get("server")),
     lambda x: ("OBSERVACION" if x[1] else "OK", f"{x[0]} faltan={x[1]}"))
resp = cli.get("/api/status")
caso("YURA-EXT-631", "web", "Cache-Control en /api/status", "GET", "no-store",
     lambda: resp.headers.get("Cache-Control"), lambda x: ("OBSERVACION" if not x else "OK", f"Cache-Control={x}"))

resumen()
volcar_matriz("../05_g06_matriz.md")
