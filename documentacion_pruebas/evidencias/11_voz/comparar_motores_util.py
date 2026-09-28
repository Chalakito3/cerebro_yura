import os, sys
sys.path.insert(0, "/home/yura/Proyecto Yura /cerebro_yura")
import texto

def correcto(tipo, esperado, oido):
    n = texto.normalizar(oido)
    if tipo == "orden": return texto.pide_orden(n, (esperado,))
    if tipo == "contiene": return texto.contiene_frase(n, esperado) or esperado in n.replace("ñ", "n") if esperado == "enseñame" else texto.contiene_frase(n, esperado)
    if tipo == "apagar": return texto.es_orden_apagar(n)
    if tipo == "afirmacion": return texto.es_afirmacion(n)
    if tipo == "quechua": return texto.respuesta_quechua_correcta(n, esperado)

