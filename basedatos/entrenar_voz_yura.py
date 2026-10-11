"""Entrena la voz de Yura para decir cada palabra quechua COMO EN LOS AUDIOS de
la docente (lo que dicen los libros), no como se escribe.

Pedido del equipo (28/09/2026): la pronunciación debe salir del audio. La voz
sintética de Yura es castellana y no puede producir k', q', ch'...; por eso
cada grabación de la docente se lleva a la voz de Yura con dos técnicas:

- "tono":   se sube el tono y el timbre de la grabación hasta el de Yura
            (ffmpeg rubberband). Conserva todos los sonidos del quechua.
- "modelo": conversión de voz kNN-VC (terceros/knn_vc): cada instante del
            audio de la docente se reemplaza por los instantes más parecidos
            de la voz de Yura. Timbre más igual al de Yura.

De cada palabra se elige la versión que el reconocedor entiende como la
palabra correcta y que más se parece al audio de la docente (DTW). Se guarda
en basedatos/pronunciaciones_yura/ (no se sube a git: sale de la voz de la
docente) y Yura la dice dentro de sus frases (pronunciaciones.partes_para_hablar).

Uso:
    python basedatos/entrenar_voz_yura.py            # palabras que faltan
    python basedatos/entrenar_voz_yura.py --rehacer  # todas otra vez
"""
import os
import shutil
import subprocess
import sys
import time
import wave
from datetime import datetime

import numpy as np

CARPETA_BASEDATOS = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(CARPETA_BASEDATOS)
sys.path.insert(0, RAIZ)
sys.path.insert(0, CARPETA_BASEDATOS)
sys.path.insert(0, os.path.join(RAIZ, "terceros", "knn_vc"))

import aprender_pronunciacion as pron  # noqa: E402
import pronunciaciones  # noqa: E402
import texto as texto_util  # noqa: E402

CARPETA_VOZ = pronunciaciones.CARPETA_VOZ_YURA
CARPETA_EVIDENCIAS = pron.CARPETA_EVIDENCIAS
TRABAJO = os.path.join(CARPETA_VOZ, "trabajo")
REFERENCIA = os.path.join(CARPETA_VOZ, "referencia_voz_yura.pt")
FRECUENCIA = 16000
FRECUENCIA_SALIDA = 24000  # la misma de la voz de Yura al reproducir
TONO_YURA_HZ = 218  # medido con la voz es-BO-SofiaNeural (28/09/2026)
TIMBRE = 1.17  # cuánto se "aclara" el timbre (voz grave -> voz de Yura)
CAPA_WAVLM = 6  # la que usa kNN-VC
VECINOS = 4


# ---------------------------------------------------------------- audio

def cargar(ruta):
    """WAV de cualquier formato -> numpy float32 mono 16 kHz (con ffmpeg)."""
    salida = subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", ruta, "-ac", "1", "-ar", str(FRECUENCIA),
         "-f", "s16le", "-"], capture_output=True, check=True, timeout=60,
    ).stdout
    return np.frombuffer(salida, dtype=np.int16).astype(np.float32) / 32768.0


def guardar(ruta, senal, frecuencia=FRECUENCIA):
    senal = np.asarray(senal, dtype=np.float32)
    pico = float(np.max(np.abs(senal))) if senal.size else 0.0
    if pico > 0:
        senal = senal * (0.9 / pico)
    with wave.open(ruta, "wb") as archivo:
        archivo.setnchannels(1)
        archivo.setsampwidth(2)
        archivo.setframerate(frecuencia)
        archivo.writeframes((np.clip(senal, -1, 1) * 32767).astype(np.int16).tobytes())


def a_frecuencia_salida(origen, destino):
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", origen, "-ac", "1",
         "-ar", str(FRECUENCIA_SALIDA), destino], check=True, timeout=60,
    )


def tono_hz(senal, frecuencia=FRECUENCIA):
    """Tono medio de la voz (autocorrelación)."""
    tramo = int(frecuencia * 0.04)
    valores = []
    for i in range(0, len(senal) - tramo, tramo // 2):
        s = senal[i:i + tramo]
        if np.sqrt((s ** 2).mean()) < 0.025:
            continue
        s = s - s.mean()
        ac = np.correlate(s, s, "full")[tramo - 1:]
        bajo, alto = int(frecuencia / 400), int(frecuencia / 70)
        k = bajo + int(np.argmax(ac[bajo:alto]))
        if ac[k] > 0.3 * ac[0]:
            valores.append(frecuencia / k)
    return float(np.median(valores)) if valores else None


# ---------------------------------------------------------------- técnica 1: tono

def por_tono(audio_docente, destino):
    senal = pron._recortar_silencio(cargar(audio_docente))
    tono = tono_hz(senal) or 140.0
    cambio_tono = max(0.5, min(2.5, TONO_YURA_HZ / tono)) / TIMBRE
    temporal = destino + ".recortado.wav"
    guardar(temporal, senal)
    filtro = (f"asetrate={int(FRECUENCIA * TIMBRE)},aresample={FRECUENCIA},"
              f"rubberband=tempo={1 / TIMBRE:.4f}:pitch={cambio_tono:.4f}:formant=preserved")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", temporal, "-af", filtro,
                    "-ac", "1", "-ar", str(FRECUENCIA), destino], check=True, timeout=60)
    os.remove(temporal)


# ---------------------------------------------------------------- técnica 2: modelo

_modelos = {}


def _knn_vc():
    if "wavlm" not in _modelos:
        import json
        import torch
        from hifigan.models import Generator
        from hifigan.utils import AttrDict
        from wavlm.WavLM import WavLM, WavLMConfig
        base = "https://github.com/bshall/knn-vc/releases/download/v0.1/"
        punto = torch.hub.load_state_dict_from_url(base + "WavLM-Large.pt", map_location="cpu", progress=False)
        wavlm = WavLM(WavLMConfig(punto["cfg"]))
        wavlm.load_state_dict(punto["model"])
        with open(os.path.join(RAIZ, "terceros", "knn_vc", "hifigan", "config_v1_wavlm.json")) as f:
            configuracion = AttrDict(json.load(f))
        vocoder = Generator(configuracion)
        vocoder.load_state_dict(torch.hub.load_state_dict_from_url(
            base + "prematch_g_02500000.pt", map_location="cpu", progress=False)["generator"])
        vocoder.eval()
        vocoder.remove_weight_norm()
        _modelos.update(wavlm=wavlm.eval(), vocoder=vocoder)
    return _modelos["wavlm"], _modelos["vocoder"]


def rasgos_wavlm(senal):
    import torch
    wavlm, _ = _knn_vc()
    with torch.inference_mode():
        return wavlm.extract_features(torch.from_numpy(senal)[None], output_layer=CAPA_WAVLM,
                                      ret_layer_results=False)[0].squeeze(0)


FRASES_REFERENCIA = [
    "Hola, soy Yura, un robot educativo que ayuda a practicar quechua.",
    "Practiquemos una palabra. Repítela, por favor.",
    "Muy bien. Lo dijiste de forma correcta.",
    "Todavía no. Inténtalo otra vez, tú puedes.",
    "¿Cómo se dice perro en quechua?",
    "Escucha con atención y di la palabra despacio.",
    "Los números, los colores, los animales y la familia.",
    "Hoy vamos a jugar, conversar y traducir juntos.",
    "Kacha, kucha, kichka, pacha, puka, tanta, chaki, chuspi, kiru, kumir.",
    "Jatun, jampatu, jallpa, juku, jak, jak, jaqay, jaku.",
    "Wasi, wawa, wayra, wakin, warmi, wira, wallpa.",
    "Allqu, llaqta, killa, pilli, tullu, kawallu, lapa.",
]


def referencia_yura():
    """Rasgos de la voz de Yura (varios minutos de su voz) para el modelo."""
    import torch
    if os.path.exists(REFERENCIA):
        return torch.load(REFERENCIA).float()
    os.makedirs(TRABAJO, exist_ok=True)
    frases = list(FRASES_REFERENCIA)
    with pronunciaciones._conectar() as conexion:
        import traductor
        for registro in traductor._leer_registros_vocabulario(conexion):
            frases.append(f"{registro['espanol']}. {pron.adaptar_al_castellano(registro['quechua'])}.")
            if registro["significado"]:
                frases.append(str(registro["significado"]))
    grupos = [" ".join(frases[i:i + 6]) for i in range(0, len(frases), 6)]
    rasgos = []
    for numero, grupo in enumerate(grupos):
        ruta = os.path.join(TRABAJO, f"referencia_{numero}.wav")
        pron.voz_de_yura(grupo, ruta)
        rasgos.append(rasgos_wavlm(cargar(ruta)))
    todos = torch.cat(rasgos, dim=0)
    torch.save(todos.half(), REFERENCIA)
    print(f"[VOZ] Referencia de la voz de Yura: {todos.shape[0] * 0.02 / 60:.1f} minutos.", flush=True)
    return todos


def por_modelo(audio_docente, destino, referencia):
    import torch
    _, vocoder = _knn_vc()
    consulta = rasgos_wavlm(pron._recortar_silencio(cargar(audio_docente)))
    normal_consulta = torch.nn.functional.normalize(consulta, dim=-1)
    normal_referencia = torch.nn.functional.normalize(referencia, dim=-1)
    similitud = normal_consulta @ normal_referencia.T
    mejores = similitud.topk(k=VECINOS, dim=-1).indices
    nuevos = referencia[mejores].mean(dim=1)
    with torch.inference_mode():
        onda = vocoder(nuevos[None]).squeeze().numpy()
    guardar(destino, onda)


# ---------------------------------------------------------------- evaluación

def evaluar(ruta, palabra, rasgos_docente, otras):
    entendida, escuchado = pron.se_entiende(ruta, palabra, otras)
    if not entendida:
        entendida = pronunciaciones.respuesta_aceptada(escuchado, palabra)
    return entendida, pron.distancia_dtw(pron.rasgos(ruta), rasgos_docente), escuchado


def entrenar(rehacer=False, informar=print):
    os.makedirs(TRABAJO, exist_ok=True)
    os.makedirs(CARPETA_EVIDENCIAS, exist_ok=True)
    with pronunciaciones._conectar() as conexion:
        hechas = {f[0] for f in conexion.execute(
            f"SELECT palabra_frase FROM {pronunciaciones.TABLA_VOZ} WHERE audio_yura IS NOT NULL")}
    por_palabra = {}
    for grabacion in pronunciaciones.grabaciones():
        por_palabra.setdefault(grabacion["palabra_frase"], grabacion)
    referencia = referencia_yura()
    resumen = {"tono": 0, "modelo": 0, "ninguna": 0, "entendidas": 0, "total": 0}
    for numero, palabra in enumerate(sorted(por_palabra), 1):
        if palabra in hechas and not rehacer:
            continue
        audio_docente = pronunciaciones.audio_de(palabra)
        if not audio_docente:
            continue
        nombre = pron._nombre_archivo(palabra)
        rasgos_docente = pron.rasgos(audio_docente)
        otras = [p for p in por_palabra if p != palabra]
        versiones = {}
        for metodo, funcion in (("tono", lambda d: por_tono(audio_docente, d)),
                                ("modelo", lambda d: por_modelo(audio_docente, d, referencia))):
            ruta = os.path.join(TRABAJO, f"{nombre}_{metodo}.wav")
            try:
                funcion(ruta)
                versiones[metodo] = (ruta,) + evaluar(ruta, palabra, rasgos_docente, otras)
            except Exception as exc:
                informar(f"  ({palabra}: la técnica {metodo} falló: {exc})")
        if not versiones:
            continue
        # Primero que se entienda; entre esas, la más parecida al audio.
        metodo = min(versiones, key=lambda m: (not versiones[m][1], versiones[m][2]))
        ruta, entendida, distancia, escuchado = versiones[metodo]
        final = os.path.join(CARPETA_VOZ, nombre + ".wav")
        a_frecuencia_salida(ruta, final)
        for otro, datos in versiones.items():
            shutil.copyfile(datos[0], os.path.join(CARPETA_EVIDENCIAS, f"{nombre}_4_yura_{otro}.wav"))
        with pronunciaciones._conectar() as conexion:
            conexion.execute(
                f"INSERT OR IGNORE INTO {pronunciaciones.TABLA_VOZ} (palabra_frase, texto_para_voz, fecha) VALUES (?, ?, ?)",
                (palabra, palabra, datetime.now().isoformat(timespec="seconds")),
            )
            conexion.execute(
                f"UPDATE {pronunciaciones.TABLA_VOZ} SET audio_yura = ?, metodo_audio = ?, "
                "audio_se_entiende = ?, audio_parecido = ?, fecha = ? WHERE palabra_frase = ?",
                (os.path.basename(final), metodo, int(entendida), distancia,
                 datetime.now().isoformat(timespec="seconds"), palabra),
            )
        resumen[metodo] += 1
        resumen["entendidas"] += int(entendida)
        resumen["total"] += 1
        detalle = " | ".join(f"{m}: {'se entiende' if v[1] else 'NO se entiende'} «{v[3]}» dist {v[2]:.3f}"
                             for m, v in versiones.items())
        informar(f"[{numero}/{len(por_palabra)}] {palabra} -> {metodo}  ({detalle})")
    shutil.rmtree(TRABAJO, ignore_errors=True)
    return resumen


if __name__ == "__main__":
    inicio = time.time()
    resumen = entrenar(rehacer="--rehacer" in sys.argv, informar=lambda t: print(t, flush=True))
    if resumen["total"]:
        print(f"\nListo en {time.time() - inicio:.0f} s: {resumen['total']} palabras; "
              f"técnica tono {resumen['tono']}, modelo {resumen['modelo']}; "
              f"se entienden {resumen['entendidas']}/{resumen['total']} = "
              f"{100 * resumen['entendidas'] / resumen['total']:.0f} %")
