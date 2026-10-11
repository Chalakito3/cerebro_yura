"""Agrega frases básicas para conversar con niños al diccionario de Yura.

Pedido del equipo (08/10/2026): que Yura aprenda lo básico para conversar con
niños y los atraiga en quechua y en castellano. Cada frase lleva las raíces
de sus palabras, y SOLO se agrega si TODAS aparecen en el Diccionario
Bilingüe de T. Laime Ajacopa (2007, documentacion_quechua/fuentes/). Los
sufijos (-m, -sqa, -sun, -chu, -taq, -y "mi") son gramática común y no se
buscan. Quedan marcadas para que la docente las revise.

Uso:  python basedatos/agregar_dialogo_ninos.py            # verifica y agrega
      python basedatos/agregar_dialogo_ninos.py --revisar  # solo muestra la verificación
"""
import os
import sqlite3
import sys
from datetime import datetime

CARPETA = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(CARPETA)
sys.path.insert(0, os.path.join(RAIZ, "documentacion_quechua", "herramientas"))
sys.path.insert(0, CARPETA)
sys.path.insert(0, RAIZ)  # antes que basedatos/: ahí hay una carpeta "pronunciaciones" de audios

from buscar_laime import buscar, secciones  # noqa: E402

TABLA = "nivel1_dialogo_infantil"
# La lista para que la docente revise está en documentacion_quechua/frases_ninos_revision_docente_2026-10-08.md
# (la nota no va en el significado: Yura lo lee en voz alta).

# (frase, traducción, significado, raíces a verificar en Laime)
FRASES = [
    # Cómo se siente
    ("Llakisqam kani", "Estoy triste", "Para decir cómo se siente", ["llakiy"]),
    ("Sayk'usqam kani", "Estoy cansado", "Para decir cómo se siente", ["sayk'uy"]),
    ("Yarqhasqam kani", "Tengo hambre", "Para pedir comida", ["yarqhay"]),
    ("Ch'akisqam kani", "Tengo sed", "Para pedir agua", ["ch'akiy"]),
    ("Unqusqam kani", "Estoy enfermo", "Para avisar que se siente mal", ["unquy"]),
    ("Manchakuni", "Tengo miedo", "Para decir que tiene miedo", ["manchakuy"]),
    # Cortesía
    ("Allillanmi, qamrí", "Bien nomás, ¿y tú?", "Respuesta a cómo estás, devolviendo la pregunta", ["allillan", "qam"]),
    ("Ama hina kaychu", "Por favor", "Para pedir algo con cortesía", ["ama", "hina", "kay"]),
    ("Yanapaway", "Ayúdame", "Para pedir ayuda", ["yanapay"]),
    # Órdenes de clase
    ("Jamuy", "Ven", "Invitación a acercarse", ["jamuy"]),
    ("Tiyakuy", "Siéntate", "Indicación en el aula", ["tiyakuy"]),
    ("Uyariy", "Escucha", "Indicación para prestar atención", ["uyariy"]),
    ("Qhawariy", "Mira", "Indicación para mirar algo", ["qhawariy"]),
    # Juego y escuela
    ("Pukllasun", "Juguemos", "Invitación a jugar", ["pukllay"]),
    ("Pukllasunchu", "¿Jugamos?", "Pregunta para invitar a jugar", ["pukllay"]),
    ("Takisun", "Cantemos", "Invitación a cantar", ["takiy"]),
    ("Yupasun", "Contemos", "Invitación a contar números", ["yupay"]),
    ("Qillqasun", "Escribamos", "Invitación a escribir", ["qillqay"]),
    # Felicitaciones
    ("Ancha allin", "Muy bien", "Felicitación", ["ancha", "allin"]),
    ("Sumaqta ruwanki", "Lo haces muy bien", "Felicitación por un trabajo", ["sumaq", "ruway"]),
    ("Kusa", "¡Qué bien!", "Exclamación de alegría", ["kusa"]),
    # Preguntas
    ("Imatataq ruwashanki", "¿Qué estás haciendo?", "Pregunta para conversar", ["ima", "ruway"]),
    ("Maypitaq tiyanki", "¿Dónde vives?", "Pregunta para conocerse", ["may", "tiyay"]),
    ("Imatataq munanki", "¿Qué quieres?", "Pregunta sobre deseos", ["ima", "munay"]),
    ("Pitaq kay", "¿Quién es este?", "Pregunta sobre una persona", ["pi", "kay"]),
    # Familia (con -y, "mi")
    ("Mamay", "Mamá, madre", "Familia", ["mama"]),
    ("Tatay", "Papá, padre", "Familia", ["tata"]),
    ("Wawqiy", "Hermano (de un varón)", "Familia (hermano de un varón)", ["wawqi"]),
    ("Ñañay", "Hermana (de una mujer)", "Familia (hermana de una mujer)", ["ñaña"]),
    # Despedidas
    ("Q'ayakama", "Hasta mañana", "Despedida", ["q'aya"]),
    ("Kunankama", "Hasta luego", "Despedida", ["kunan"]),
]


def _en_laime(raiz, quechua, castellano, palabras_libro):
    """La raíz es entrada del diccionario quechua-castellano, o Laime la da
    como traducción en la parte castellano-quechua ("tú. pron. Qam") o como
    sinónimo dentro de una definición ("sinón: Allillan")."""
    return bool(buscar(raiz, quechua)) or raiz.lower() in palabras_libro


def verificar():
    import re
    from buscar_laime import _texto
    quechua, castellano = secciones()
    palabras_libro = set(re.findall(r"[a-zñ']+", _texto().lower().replace("’", "'")))
    resultado = []
    for frase, traduccion, significado, raices in FRASES:
        faltan = [r for r in raices if not _en_laime(r, quechua, castellano, palabras_libro)]
        resultado.append((frase, traduccion, significado, faltan))
    return resultado


def agregar(verificadas):
    import pronunciaciones
    from ampliar_vocabulario_dialogo import fonetica_quechua_oficial

    ahora = datetime.now().isoformat(timespec="seconds")
    agregadas = 0
    with sqlite3.connect(pronunciaciones.RUTA_DB) as conexion:
        existentes = {fila[0].strip().lower() for fila in conexion.execute(f"SELECT palabra_frase FROM {TABLA}")}
        for frase, traduccion, significado, _ in verificadas:
            if frase.lower() in existentes:
                continue
            conexion.execute(
                f"INSERT INTO {TABLA} (palabra_frase, pronunciacion, traduccion, significado) VALUES (?, ?, ?, ?)",
                (frase, None, traduccion, significado),  # la nota de revisión va en la lista para la docente
            )
            conexion.execute(
                "INSERT OR IGNORE INTO pronunciaciones_voz (palabra_frase, texto_para_voz, fecha, metodo_audio, fijada) "
                "VALUES (?, ?, ?, 'oficial_laime', 0)",
                (frase, fonetica_quechua_oficial(frase), ahora),
            )
            agregadas += 1
    return agregadas


if __name__ == "__main__":
    resultado = verificar()
    verificadas = [r for r in resultado if not r[3]]
    for frase, traduccion, _, faltan in resultado:
        estado = "✓" if not faltan else f"✗ no está en Laime: {', '.join(faltan)}"
        print(f"  {estado:40} {frase} = {traduccion}")
    print(f"\nVerificadas: {len(verificadas)} de {len(resultado)}")
    if "--revisar" not in sys.argv:
        print(f"Agregadas al diccionario: {agregar(verificadas)}")
