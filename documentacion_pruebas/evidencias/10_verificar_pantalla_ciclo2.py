"""Verifica la pantalla del robot (ciclo 2) en Firefox con un robot falso.
Mide si el contenido cabe en 1920x1080, 1024x600 y 800x480 y guarda capturas."""
import os, sys, time
RAIZ = "/home/yura/Proyecto Yura /cerebro_yura"
sys.path.insert(0, os.path.join(RAIZ, "documentacion_pruebas/evidencias/02_frontend_datos"))
from wd import S, setfake, APP

MEDIR = """
const r = s => { const e = document.querySelector(s); if (!e || e.offsetParent === null) return null; const b = e.getBoundingClientRect(); return [Math.round(b.top), Math.round(b.bottom)]; };
return {alto: innerHeight, desborde_x: document.documentElement.scrollWidth > innerWidth,
  modo: document.querySelector('#activity').textContent, contenido: document.querySelector('#content-main').textContent,
  traduccion: document.querySelector('#content-translation').textContent, resultado: document.querySelector('#content-result').textContent,
  tarjeta: document.querySelector('#word-title').textContent + ' = ' + document.querySelector('#word-meaning').textContent,
  pie: document.querySelector('#updated').textContent,
  caja_contenido: r('#content-main'), caja_resultado: r('#content-result'), caja_tarjeta: r('.word-card')};
"""
escenarios = [
    ("juego_correcto", dict(state="JUEGO", phase="CELEBRANDO", content="Allqu", translation="perro", result="CORRECTO")),
    ("juego_incorrecto", dict(state="JUEGO", phase="TRISTE", content="Jamp'ara", translation="mesa", result="INCORRECTO")),
    ("traductor_nino", dict(state="TRADUCIR", phase="HABLANDO", content="Irqi", translation="Niño", result=None)),
]
s = S()
try:
    for ancho, alto in [(1920, 1080), (1024, 600), (800, 480)]:
        s.size(ancho, alto)
        s.go(APP + "/")
        time.sleep(1.5)
        for nombre, estado in escenarios:
            setfake(**estado)
            s.js("refreshStatus();"); time.sleep(0.8)
            m = s.js(MEDIR)
            cabe = all(c is None or c[1] <= m["alto"] for c in (m["caja_contenido"], m["caja_resultado"], m["caja_tarjeta"]))
            print(f"{ancho}x{alto} {nombre:17} cabe={cabe} desborde_x={m['desborde_x']} | modo={m['modo']} | {m['contenido']} / {m['traduccion']} {m['resultado']} | tarjeta: {m['tarjeta']} | pie: {m['pie']}")
            if nombre == "juego_correcto":
                s.shot(os.path.join(RAIZ, f"documentacion_pruebas/evidencias/10_pantalla_{ancho}x{alto}_juego.png"))
    s.size(1024, 600)
    setfake(none=True)
    s.js("refreshStatus();"); time.sleep(0.8)
    setfake(fail_status=True)
    s.js("refreshStatus();"); time.sleep(0.8)
    m = s.js(MEDIR)
    print(f"sin conexión: contenido={m['contenido']!r} traduccion={m['traduccion']!r} tarjeta={m['tarjeta']!r}")
    s.shot(os.path.join(RAIZ, "documentacion_pruebas/evidencias/10_pantalla_sin_conexion.png"))
    setfake(fail_status=False)
finally:
    s.quit()
