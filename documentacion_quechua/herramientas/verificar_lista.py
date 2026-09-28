"""Verifica en el diccionario de Laime las palabras del documento de vocabulario.

Uso: python verificar_lista.py  (escribe el resultado en laime_verificacion.txt)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from buscar_laime import buscar, secciones

QUECHUA = """
allin p'unchay|p'unchay|sukha|allin sukha|allin tuta|tuta|imaynalla|allinlla|rimaykullayki|rimaykuy|yusulpayki|sulpayki|tupananchikkama|tupananchiskama|ari|mana
qanchis|pusaq|waranqa|pachak|suqta|phichqa|pichqa|jisq'un|juk|iskay|kimsa|tawa|chunka
llimp'i|puka|q'illu|q'umir|anqas|ch'umpi|kulli|quri|ch'iqchi|uqi|yuraq|yana|qullqi
tata|mama|wawa|wawqi|ñaña|tura|pana|jatun tata|jatun mama|qhari|warmi|runa|imilla|irqi|yachachiq|yachakuq
uma|uya|ñawi|sinqa|simi|rinri|kiru|chukcha|kunka|wiksa|sunqu|maki|tullu|aycha|chaki|qallu|wasa|ruk'ana
allqu|misi|waka|khuchi|uwija|wallpa|k'anka|pilli|kututu|quwi|k'usillu|q'alachu|juku|yuthu|anka|chawlla|challwa|ch'uspi|khuru|llama|kuntur|atuq|taruka|pillpintu|jamp'atu|amaru|ukucha|ukuku|ninakuru|wallata
mikhuy|upyay|t'anta|sara|papa|runtu|kanka|misk'i|yaku|unu|uchu|api|aswa|jank'a|mullu
inti|killa|nina|para|phuyu|wayra|rumi|qucha|t'ika|k'aspi|pampa|urqu|ñan|mayu|sach'a|ch'aska|allpa|janaq pacha
wasi|chuwa|q'uncha|p'acha|yachaywasi|yachana wasi|yachaqana wasi|jamp'ara|tiyana|p'anqa|qillqana|llaqta|qhatu|punku|manka|chaka|yawri|q'ipi
jatun|juch'uy|k'acha|saqra|millay|wira|kusisqa|q'uñi|chiri|musuq|machu|kay|chay|jaqay
"""

CASTELLANO = """
agua|nariz|diente|espalda|hueso|mano|venado|mono|luciérnaga|caliente|puente|sendero|escuela|aula|aguja|mesa|pizarra|horno|hacha|olla|mirador|abeja|avispa|lagarto|lagartija|jardín|sartén|pala|ventana|naranja|rosado|celeste|opaco|talón|pantorrilla|dedo|cabello|pato|cuy|pez|pueblo|plato|libro|cuaderno|mochila|bolígrafo|lápiz|maíz|ají|chicha|gato montés|mariposa|gris|azul|verde|amarillo|rojo|blanco|negro|marrón|morado|gracias|buenos días|tarde|noche|hermano|hermana|abuelo|abuela|niño|niña|mil|ocho|siete|dieciocho|once
"""


def lista(bloque):
    return [p.strip() for linea in bloque.strip().splitlines() for p in linea.split("|") if p.strip()]


if __name__ == "__main__":
    quechua, castellano = secciones()
    salida = []
    for titulo, palabras, fuente in (
        ("QUECHUA → CASTELLANO", lista(QUECHUA), quechua),
        ("CASTELLANO → QUECHUA", lista(CASTELLANO), castellano),
    ):
        salida.append(f"\n===== {titulo} =====")
        for palabra in palabras:
            resultados = buscar(palabra, fuente)
            salida.append(f"■ {palabra}: " + (" ‖ ".join(resultados) if resultados else "NO ENCONTRADA"))
    destino = os.path.join(os.path.dirname(os.path.abspath(__file__)), "laime_verificacion.txt")
    open(destino, "w", encoding="utf-8").write("\n".join(salida) + "\n")
    print("\n".join(salida))
