"""Captura la página /resultados con datos de demostración (no toca resultados.db)."""
import os, sys, threading, time
RAIZ = "/home/yura/Proyecto Yura /cerebro_yura"
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "documentacion_pruebas/evidencias/02_frontend_datos"))
import resultados
demo = os.path.join(RAIZ, "documentacion_pruebas/evidencias/09_resultados_demo.db")
if os.path.exists(demo):
    os.remove(demo)
resultados.RUTA_DB = demo
ejemplos = [
    ("juego", "perro", "Allqo", "allqo", True), ("juego", "gato", "Misi", "michi", False),
    ("juego", "sol", "Inti", "inti", True), ("juego", "casa", "Wasi", "wasi", True),
    ("practica", "niño", "Wawa", "wawa", True), ("practica", "mariposa", "Pillpintu", "pilpintu", True),
    ("practica", "gato", "Misi", "misi", True), ("juego", "gato", "Misi", "gatu", False),
    ("practica", "ojo", "Ñawi", "nawi", True), ("juego", "árbol", "Sach'a", "sacha", True),
]
for actividad, es, qu, resp, ok in ejemplos:
    resultados.registrar_intento(actividad, es, qu, resp, ok, actividad[:1] + "1")
import web.app as webapp
threading.Thread(target=lambda: webapp.app.run(port=5052), daemon=True).start()
time.sleep(2)
from wd import S
s = S()
try:
    for ancho, alto, nombre in [(1366, 900, "escritorio"), (390, 844, "celular")]:
        s.size(ancho, alto)
        s.go("http://127.0.0.1:5052/resultados")
        time.sleep(1.5)
        s.shot(os.path.join(RAIZ, f"documentacion_pruebas/evidencias/09_resultados_{nombre}.png"), full=True)
        print(nombre, "desborde horizontal:", s.js("return document.documentElement.scrollWidth > innerWidth"))
finally:
    s.quit()
