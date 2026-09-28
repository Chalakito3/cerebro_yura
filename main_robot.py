#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import queue
import re
import sqlite3
import shutil
import threading
import traceback
from datetime import datetime, timezone
import texto as texto_util
import depuracion
import traductor
import subprocess
import ctypes
import wave
import time
import tempfile
import whisper
from groq import Groq
import conversacion
import pronunciaciones
from audio_manager import AudioManager
from juego import Juego
from gemini_transcriber import GeminiTranscriber


# ============================================================
# SILENCIAR REPORTES MOLESTOS DE ALSA EN UBUNTU
# ============================================================

try:
    ERROR_HANDLER_FUNC = ctypes.CFUNCTYPE(
        None,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p
    )

    def py_error_handler(filename, line, function, err, fmt):
        pass

    c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)

    asound = ctypes.CDLL("libasound.so.2")
    asound.snd_lib_error_set_handler(c_error_handler)

except Exception:
    pass


# ============================================================
# CARGAR CLAVES DESDE .env.local
# ============================================================

def cargar_archivo_claves():
    """Carga las variables de .env.local sin pisar las ya definidas."""
    base_dir = os.path.dirname(os.path.abspath(__file__))

    for nombre in (".env.local", ".env"):
        ruta = os.path.join(base_dir, nombre)
        if not os.path.isfile(ruta):
            continue
        try:
            with open(ruta, "r", encoding="utf-8-sig", errors="ignore") as fh:
                for linea in fh:
                    texto = linea.strip()
                    if not texto or texto.startswith("#") or "=" not in texto:
                        continue
                    if texto.startswith("export "):
                        texto = texto[len("export "):]
                    clave, valor = texto.split("=", 1)
                    clave = clave.strip()
                    valor = valor.strip().strip("\"'")
                    if clave and valor:
                        os.environ.setdefault(clave, valor)
            print(f"[OK]: Claves cargadas desde '{nombre}'.")
        except Exception as exc:
            print(f"[ALERTA CLAVES]: No se pudo leer '{nombre}': {exc}")


class ApagadoConfirmado(Exception):
    """Se confirmó por voz la orden de apagar: termina el ciclo principal."""


class ModoDocentePedido(Exception):
    """La docente presionó "Activar modo docente": se corta lo que se estaba
    haciendo para no hacerla esperar."""


# ============================================================
# ESTADOS DEL ROBOT
# ============================================================

class RobotStates:
    MENU = "MENU"
    CONVERSAR = "CONVERSAR"
    JUEGO = "JUEGO"
    TRADUCIR = "TRADUCIR"
    SILENCIO = "SILENCIO"
    ENSENAR = "ENSENAR"
    SALIR = "SALIR"


# ============================================================
# INTERFAZ DE HARDWARE
# ============================================================

class HardwareInterface:

    def __init__(self, audio_manager=None, on_status=None):
        descriptor, self.audio_temp = tempfile.mkstemp(
            prefix="yura-",
            suffix=".mp3"
        )
        os.close(descriptor)
        # Voz boliviana elegida por el equipo (27/09/2026); antes era mexicana
        # (es-MX-DaliaNeural). Se puede cambiar con YURA_VOZ en .env.local.
        self.voz_mujer = os.environ.get("YURA_VOZ", "es-BO-SofiaNeural").strip() or "es-BO-SofiaNeural"
        self.audio_manager = audio_manager
        self.on_status = on_status

    def _formatear_texto_voz(self, texto):
        if texto is None:
            return ""

        texto = str(texto).strip()
        texto = re.sub(r"\s+", " ", texto)
        texto = texto.replace("¿", "")
        texto = texto.replace("¡", "")
        texto = texto.replace("?", ".")
        texto = texto.replace("!", ".")

        if not re.search(r"[.,;:]$", texto):
            texto = texto + "."

        texto = texto.replace(" y ", ", y ")
        texto = texto.replace(" pero ", ". Pero ")
        texto = texto.replace(" entonces ", ". Entonces ")
        texto = texto.replace(" por favor ", ", por favor, ")

        return texto.strip()

    def _limpiar_texto_tts(self, texto):
        if texto is None:
            return ""

        texto = str(texto)
        texto = texto.replace("```", "")
        texto = re.sub(r"^\s{0,3}#{1,6}\s*", "", texto, flags=re.MULTILINE)
        texto = re.sub(r"^\s*[-+]\s+", "", texto, flags=re.MULTILINE)
        texto = re.sub(r"\*\*(.*?)\*\*", r"\1", texto, flags=re.DOTALL)
        texto = re.sub(r"\*(.*?)\*", r"\1", texto, flags=re.DOTALL)
        texto = texto.replace("_", " ")
        texto = texto.replace("`", "")
        texto = re.sub(r"\s+", " ", texto)
        return texto.strip()

    def _notify_status(self, phase, **data):
        if not self.on_status:
            return
        try:
            self.on_status(phase, **data)
        except Exception:
            pass

    def _destino_pipewire_predeterminado(self):
        wpctl = shutil.which("wpctl")
        if not wpctl:
            return None
        try:
            resultado = subprocess.run(
                [wpctl, "inspect", "@DEFAULT_AUDIO_SINK@"],
                capture_output=True,
                text=True,
                check=False,
                timeout=2
            )
        except (OSError, subprocess.SubprocessError):
            return None

        if resultado.returncode != 0:
            return None
        coincidencia = re.search(
            r"^\s*\*?\s*object\.serial\s*=\s*\"?(\d+)",
            resultado.stdout,
            flags=re.MULTILINE
        )
        return coincidencia.group(1) if coincidencia else None

    def _texto_visible(self, texto):
        original = str(texto or "").strip()
        if not original:
            return ""

        texto_limpio = self._limpiar_texto_tts(original)
        if not texto_limpio:
            return ""

        coincidencia = re.match(
            r"^En quechua (?:se dice|se puede decir)\s*:?\s*(.+)$",
            texto_limpio,
            flags=re.IGNORECASE
        )
        if coincidencia:
            traduccion = coincidencia.group(1).strip()
            return traduccion.split(". ", 1)[0].strip(" .")

        return texto_limpio.split(". ", 1)[0].strip(" .")

    def hablar(self, texto):
        if not texto:
            return

        texto_limpio = self._limpiar_texto_tts(texto)
        texto_voz = self._formatear_texto_voz(texto_limpio)
        texto_visible = self._texto_visible(texto_limpio)
        print(f"\n[YURA HABLA]: {texto_voz}")
        self._notify_status(
            "HABLANDO",
            content=texto_visible,
            translation=texto_visible
        )

        try:
            # ----------------------------------------------------
            # EDGE TTS
            # ----------------------------------------------------
            try:
                edge_tts = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    ".venv",
                    "bin",
                    "edge-tts"
                )
                if not os.path.exists(edge_tts):
                    edge_tts = "edge-tts"

                cmd_tts = [
                    edge_tts,
                    "--voice",
                    self.voz_mujer,
                    "--rate=+5%",
                    "--text",
                    texto_voz,
                    "--write-media",
                    self.audio_temp
                ]

                # Sin tiempo máximo, una red colgada bloquearía a Yura.
                espera_reproduccion = 30 + len(texto_voz) / 10

                res = None
                for intento in range(2):
                    try:
                        res = subprocess.run(
                            cmd_tts,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            timeout=20
                        )
                    except subprocess.TimeoutExpired:
                        print("[AUDIO] Edge TTS no respondió a tiempo.")
                        res = None
                        continue
                    if (
                        res.returncode == 0
                        and os.path.exists(self.audio_temp)
                        and os.path.getsize(self.audio_temp) > 0
                    ):
                        break
                    if intento == 0:
                        print("[AUDIO] Edge TTS falló; reintentando una vez...")

                if (
                    res is None
                    or res.returncode != 0
                    or not os.path.exists(self.audio_temp)
                    or os.path.getsize(self.audio_temp) == 0
                ):
                    codigo = res.returncode if res is not None else "desconocido"
                    print(f"[AUDIO] Edge TTS no generó voz (código {codigo}).")
                    raise RuntimeError("Falló la generación de voz con Edge TTS")

                wav_temp = f"{self.audio_temp}.wav"
                ffmpeg = shutil.which("ffmpeg")
                pw_play = shutil.which("pw-play")
                reproductores = []

                if ffmpeg and pw_play:
                    conversion = subprocess.run(
                        [
                            ffmpeg,
                            "-hide_banner",
                            "-loglevel",
                            "error",
                            "-y",
                            "-i",
                            self.audio_temp,
                            "-acodec",
                            "pcm_s16le",
                            "-ar",
                            "24000",
                            "-ac",
                            "1",
                            wav_temp
                        ],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=15
                    )
                    if conversion.returncode == 0 and os.path.exists(wav_temp):
                        destino = self._destino_pipewire_predeterminado()
                        comando_pw = [pw_play]
                        if destino:
                            comando_pw.extend(["--target", destino])
                        comando_pw.append(wav_temp)
                        reproductores.append(comando_pw)

                ffplay = shutil.which("ffplay")
                if ffplay:
                    reproductores.append([
                        ffplay,
                        "-nodisp",
                        "-autoexit",
                        "-loglevel",
                        "error",
                        self.audio_temp
                    ])

                mpg123 = shutil.which("mpg123")
                if mpg123 and self.audio_manager and self.audio_manager.output_alsa_device:
                    reproductores.append([
                        mpg123,
                        "-q",
                        "-a",
                        self.audio_manager.output_alsa_device,
                        self.audio_temp
                    ])
                elif mpg123:
                    reproductores.append([
                        mpg123,
                        "-q",
                        self.audio_temp
                    ])

                for reproductor in reproductores:
                    try:
                        reproduccion = subprocess.run(
                            reproductor,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            timeout=espera_reproduccion
                        )
                    except subprocess.TimeoutExpired:
                        print(
                            f"[AUDIO] {os.path.basename(reproductor[0])} "
                            "no terminó a tiempo; probando otra salida."
                        )
                        continue
                    except OSError as exc:
                        print(f"[AUDIO] No se pudo iniciar el reproductor: {exc}")
                        continue
                    if reproduccion.returncode != 0:
                        print(
                            f"[AUDIO] Falló {os.path.basename(reproductor[0])}; "
                            "probando otra salida."
                        )
                        continue

                    for archivo in (self.audio_temp, wav_temp):
                        try:
                            os.remove(archivo)
                        except OSError:
                            pass
                    return

                print("[AUDIO] Ningún reproductor disponible pudo emitir la voz.")
            except Exception as exc:
                print(f"[AUDIO] Error al generar o reproducir la voz: {exc}")

            spd_say = shutil.which("spd-say")
            if spd_say:
                resultado = subprocess.run(
                    [spd_say, "-l", "es", "-t", "female1", "-w", texto_voz],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=60
                )
                if resultado.returncode != 0:
                    print("[AUDIO] Speech Dispatcher no pudo reproducir la voz.")
            else:
                espeak = shutil.which("espeak")
                if espeak:
                    subprocess.run(
                        [espeak, "-v", "es-la", "-s", "140", texto_voz],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=60
                    )
                else:
                    print("[AUDIO] No hay un motor de voz local disponible.")
        except Exception:
            pass
        finally:
            for archivo in (self.audio_temp, f"{self.audio_temp}.wav"):
                try:
                    os.remove(archivo)
                except OSError:
                    pass
            self._notify_status("ESPERANDO")

    def reproducir_grabacion(self, ruta):
        """Reproduce un archivo WAV (la voz de la docente) por la salida
        de audio actual."""
        if not ruta or not os.path.exists(ruta):
            return False
        self._notify_status("HABLANDO")
        comandos = []
        pw_play = shutil.which("pw-play")
        if pw_play:
            destino = self._destino_pipewire_predeterminado()
            comandos.append([pw_play] + (["--target", destino] if destino else []) + [ruta])
        ffplay = shutil.which("ffplay")
        if ffplay:
            comandos.append([ffplay, "-nodisp", "-autoexit", "-loglevel", "error", ruta])
        try:
            for comando in comandos:
                try:
                    resultado = subprocess.run(
                        comando, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20
                    )
                except (subprocess.TimeoutExpired, OSError):
                    continue
                if resultado.returncode == 0:
                    return True
            print("[AUDIO] No se pudo reproducir la grabación de la docente.")
            return False
        finally:
            self._notify_status("ESPERANDO")

    def mover_actuador(self, comando):
        print(f"[FISICO]: Motores ejecutando -> {comando}")


# ============================================================
# CEREBRO DE YURA
# ============================================================

class BrainYura:

    def __init__(self):

        cargar_archivo_claves()

        # ----------------------------------------------------
        # ESTADO GENERAL
        # ----------------------------------------------------

        self.state = RobotStates.MENU
        self.running = True
        self.historial_conversacion = []
        self.web_status = {
            "phase": "ESPERANDO",
            "content": "Rimaykullayki",
            "translation": "",
            "result": None,
            "updated_at": None,
        }
        self.web_status_lock = threading.Lock()

        # Modo docente: la página /ensenar lo activa y pide grabaciones.
        self.pedido_docente = threading.Event()
        self.ordenes_docente = queue.Queue()
        self.ensenanza = {"estado": "inactivo"}
        self.ultima_actividad_docente = 0.0

        self.audio_manager = AudioManager()
        self.hw = HardwareInterface(
            self.audio_manager,
            on_status=self._set_web_status
        )
        # "small" entendió 77-93 % de las frases de prueba; "base", 70 % (27/09/2026).
        whisper_name = os.environ.get("YURA_WHISPER_MODEL", "small").strip() or "small"
        print(f"[WHISPER]: Cargando modelo {whisper_name}...")
        self.whisper_model = whisper.load_model(whisper_name)
        print(f"[WHISPER]: Modelo cargado {whisper_name}.")
        self.gemini_transcriber = GeminiTranscriber()

        # ----------------------------------------------------
        # BASE DE DATOS
        # ----------------------------------------------------

        self.db_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "diccionario.db"
        )

        self.db_conn = None
        self.groq_client = self._crear_cliente_groq()

        # ----------------------------------------------------
        # CONTROL DEL MENÚ
        # ----------------------------------------------------

        self.saludo_inicial_done = False

        # ----------------------------------------------------
        # MICRÓFONO
        # ----------------------------------------------------

        self._buscar_headset_usb()

        # ----------------------------------------------------
        # SISTEMAS LOCALES
        # ----------------------------------------------------

        self.inicializar_sistemas_locales()
        self.juego = Juego(
            lambda: traductor.palabras_para_juego(self.db_conn),
            lambda palabra: traductor.consultar_diccionario_local(
                palabra,
                self.db_conn
            ),
            self._escuchar_con_ordenes,
            self.hw.hablar,
            self._mover_actuador,
            self._normalizar_texto,
            self._set_game_event,
            reproducir_pronunciacion=self._reproducir_pronunciacion,
        )

    def _set_web_status(
        self,
        phase,
        content=None,
        translation=None,
        result=None,
        fijar=False
    ):
        """Actualiza lo que muestra la pantalla.

        Con fijar=True el contenido (palabra quechua y su significado) queda
        en pantalla mientras Yura habla, en lugar de la primera frase de lo
        que dice; se libera cuando vuelve a escuchar.
        """
        with self.web_status_lock:
            self.web_status["phase"] = phase
            if phase == "ESCUCHANDO":
                self.web_status["fijo"] = False
            actualizar = fijar or not self.web_status.get("fijo")
            if fijar:
                self.web_status["fijo"] = True
            if content is not None and actualizar:
                self.web_status["content"] = str(content).strip()
            if translation is not None and actualizar:
                self.web_status["translation"] = str(translation).strip()
            if result is not None:
                self.web_status["result"] = result
            self.web_status["updated_at"] = datetime.now(timezone.utc).isoformat()

    def get_web_status(self):
        with self.web_status_lock:
            estado = dict(self.web_status)
        estado.pop("fijo", None)
        return estado

    def _mover_actuador(self, comando):
        if comando == "CELEBRAR_ALEGRE":
            self._set_web_status("CELEBRANDO", result="CORRECTO")
        elif comando == "TRISTE":
            self._set_web_status("TRISTE", result="INCORRECTO")
        self.hw.mover_actuador(comando)

    def _set_game_event(self, event, **data):
        if event == "question":
            self._set_web_status(
                "PENSANDO",
                content=data.get("question", ""),
                translation="",
                result=None
            )
        elif event == "result":
            # Se muestra la palabra correcta y su significado, no la pregunta.
            self._set_web_status(
                "CELEBRANDO" if data.get("correct") else "TRISTE",
                content=data.get("answer", ""),
                translation=data.get("word", ""),
                result="CORRECTO" if data.get("correct") else "INCORRECTO",
                fijar=True
            )

    # ========================================================
    # CARGAR MODELO VOSK
    # ========================================================


    def _buscar_headset_usb(self):
        self.dispositivo_index = self.audio_manager.input_device

        if self.dispositivo_index is None:
            print(
                "[ALERTA MICROFONO]: "
                "No se encontró una entrada de audio compatible."
            )

    # ========================================================
    # INICIALIZAR SQLITE
    # ========================================================

    def inicializar_sistemas_locales(self):

        if not os.path.isfile(self.db_path):
            self.db_conn = None
            print(
                f"[ALERTA BD]: No existe '{self.db_path}'. "
                "Copia diccionario.db en la carpeta del proyecto; "
                "sin él no hay vocabulario ni traductor local."
            )
            return

        try:

            self.db_conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False
            )

            print(
                f"[OK]: Base de datos "
                f"'{os.path.basename(self.db_path)}' enlazada."
            )

        except Exception as exc:

            self.db_conn = None

            print(
                f"[ALERTA BD]: "
                f"Error abriendo el archivo .db: {exc}"
            )

    def _obtener_api_key_groq(self):
        # La clave viene del entorno o de .env.local (cargar_archivo_claves).
        # Antes también se ejecutaban bash/zsh con shell=True para leer
        # .bashrc, .profile y .zshrc: innecesario y riesgoso.
        return os.environ.get("GROQ_API_KEY", "").strip()

    def _crear_cliente_groq(self):

        api_key = self._obtener_api_key_groq()

        if not api_key:
            print(
                "[ALERTA GROQ]: "
                "GROQ_API_KEY no está en el entorno ni en .env.local. "
                "El fallback online queda deshabilitado."
            )
            return None

        try:
            os.environ["GROQ_API_KEY"] = api_key
            # Tiempo máximo corto: con la red colgada, el SDK esperaba hasta
            # 60 s y reintentaba dos veces, y Yura quedaba muda minutos.
            cliente = Groq(api_key=api_key, timeout=10.0, max_retries=1)
            print("[OK GROQ]: Cliente Groq inicializado desde la configuración disponible del entorno.")
            return cliente
        except Exception as exc:
            print(
                f"[ERROR GROQ]: "
                f"No se pudo crear el cliente: {exc}"
            )
            return None

    # ========================================================
    # NORMALIZAR TEXTO
    # ========================================================

    def _normalizar_texto(self, texto):
        # Conserva ñ y apóstrofo: "ñuqa" y "p'unchay" no deben deformarse.
        return texto_util.normalizar(texto)

    # ========================================================
    # ESCUCHAR VOZ
    #
    # CONTRATO ABSOLUTO:
    #
    #   Voz reconocida correctamente -> texto
    #
    #   CUALQUIER ERROR:
    #       ""
    #
    # Nunca devuelve una respuesta inventada.
    # Nunca consulta el diccionario para simular una respuesta.
    # ========================================================

    def escuchar_voz(self, solo_local=False, pistas=None, guardar_audio_en=None):
        self._revisar_pedido_docente()

        self._set_web_status("ESCUCHANDO")
        depuracion.depurar(
            f"[DEBUG AUDIO] iniciando escucha state={self.state} "
            f"device={self.audio_manager.input_device} "
            f"device_index={self.dispositivo_index}"
        )

        if self.dispositivo_index is None:
            print("[AUDIO] Índice inicial no disponible; AudioManager reenumerará el JACK.")

        depuracion.depurar(f"[YURA ESCUCHA] micrófono índice {self.dispositivo_index}")

        try:
            time.sleep(0.3)
            depuracion.depurar(
                "[DEBUG AUDIO] captura iniciada "
                f"device={self.audio_manager.input_device}"
            )
            depuracion.depurar("[DEBUG AUDIO] antes de esperar audio")
            audio_bytes = self.audio_manager.grabar_hasta_silencio(
                espera_maxima=10.0,
                duracion_maxima=15.0,
                silencio_final=1.0,
                bloque_ms=80
            )
            depuracion.depurar("[DEBUG AUDIO] después de recibir audio")
            depuracion.depurar("[DEBUG AUDIO] captura finalizada")
            depuracion.depurar(
                "[DEBUG AUDIO] audio recibido: "
                f"{0 if audio_bytes is None else len(audio_bytes)} bytes"
            )

        except Exception as exc:
            print(f"[ERROR MICROFONO]: {exc}")
            depuracion.depurar(f"[DEBUG AUDIO] excepción durante captura: {type(exc).__name__}")
            self._set_web_status("ESPERANDO")
            return ""

        self._revisar_pedido_docente()

        if not audio_bytes:
            self.dispositivo_index = self.audio_manager.input_device
            depuracion.depurar("[YURA]: No se capturó audio.")
            self._set_web_status("ESPERANDO")
            return ""

        self.dispositivo_index = self.audio_manager.input_device
        self._set_web_status("PENSANDO")

        audio_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "yura_temp.wav"
        )

        try:
            motor_transcripcion = "ninguno"
            with wave.open(audio_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(audio_bytes + b"\x00" * int(16000 * 2 * 0.25))
            if guardar_audio_en:
                pronunciaciones.guardar_wav(guardar_audio_en, audio_bytes)

            # En silencio no se envía la voz a la nube: solo Whisper local.
            instruccion = texto_util.instruccion_reconocedor(pistas)
            texto_gemini = None if solo_local else self.gemini_transcriber.transcribir(audio_path, instruccion)
            if texto_gemini:
                motor_transcripcion = "Gemini"
                texto = self._normalizar_texto(texto_gemini)
                depuracion.voz("[GEMINI ESCUCHÓ]", texto)
            elif self.whisper_model is not None:
                motor_transcripcion = "Whisper"
                depuracion.depurar("[WHISPER]: Fallback de precisión activado.")
                depuracion.depurar("[DEBUG AUDIO] enviando audio a Whisper")
                inicio_whisper = time.perf_counter()
                resultado = self.whisper_model.transcribe(
                    audio_path,
                    language="es",
                    initial_prompt=instruccion,
                    fp16=False,
                    temperature=0,
                    beam_size=5,
                    best_of=1,
                    without_timestamps=True,
                    condition_on_previous_text=False
                )
                depuracion.depurar("[DEBUG AUDIO] Whisper respondió")
                print(
                    f"[WHISPER]: procesamiento en "
                    f"{time.perf_counter() - inicio_whisper:.1f}s"
                )
                texto = self._normalizar_texto(
                    resultado.get("text", "")
                )
            else:
                texto = ""

        except Exception as exc:
            print(f"[ERROR WHISPER]: {exc}")
            depuracion.depurar(f"[DEBUG AUDIO] excepción durante Whisper: {type(exc).__name__}")
            texto = ""
        finally:
            try:
                if os.path.exists(audio_path):
                    os.remove(audio_path)
            except Exception:
                pass

        if texto_util.es_alucinacion_whisper(texto):
            depuracion.voz("[YURA]: Se descarta una frase inventada por el reconocedor", texto)
            texto = ""

        if texto == "":
            print("[YURA]: No logré escuchar ninguna palabra.")
            depuracion.depurar("[DEBUG AUDIO] Whisper no produjo texto")
            self._set_web_status("ESPERANDO")
            return ""

        depuracion.voz(f"[TRANSCRIPCIÓN FINAL - {motor_transcripcion}]", texto)
        depuracion.depurar("[DEBUG AUDIO] texto listo; devolviendo al estado actual")
        return texto

    # ========================================================
    # MENÚ PRINCIPAL
    # ========================================================

    def ejecutar_menu(self):

        # ----------------------------------------------------
        # PREGUNTA DEL MENÚ
        # ----------------------------------------------------

        if not self.saludo_inicial_done:
            self.saludo_inicial_done = True
            saludo = conversacion.PRESENTACION_YURA
            self._set_web_status("ESPERANDO", content=saludo, translation="")
            self.hw.hablar(saludo)

        # ----------------------------------------------------
        # ESCUCHAR
        # ----------------------------------------------------

        opcion = self._escuchar_con_ordenes()

        # ====================================================
        # REGLA CRÍTICA:
        #
        # "" NO SIGNIFICA "JUGAR"
        #
        # "" NO SIGNIFICA NINGUNA OPCIÓN.
        #
        # SE REPITE EL MENÚ.
        # ====================================================

        if opcion == "":
            self.state = RobotStates.MENU
            self._set_web_status("ESPERANDO", content=conversacion.PRESENTACION_YURA, translation="")
            return

        # ----------------------------------------------------
        # NORMALIZAR
        # ----------------------------------------------------

        opcion = self._normalizar_texto(opcion)

        # Segunda barrera de seguridad.

        if opcion == "":
            self.state = RobotStates.MENU
            return

        comando = re.sub(r"^yura\s+", "", opcion).strip()

        # Las preguntas de idioma van primero: en "¿cómo se dice adiós?" o
        # "¿cómo se dice apagar?" la palabra se consulta, no se ejecuta.
        if texto_util.es_pregunta_de_idioma(comando):
            self._responder_conversacion(
                conversacion.procesar_entrada(opcion, self.groq_client)
            )
            return

        if texto_util.pide_orden(
            comando, ("presentate", "presentarte", "quien eres")
        ):
            self.hw.hablar(
                conversacion.PRESENTACION_YURA
            )
            self.state = RobotStates.MENU
            return

        if (
            texto_util.pide_orden(
                comando,
                ("silencio", "silenciate", "callate", "quedate callada")
            )
            or comando == "espera"
            or comando.startswith("espera ")
        ):
            self.hw.hablar(
                "Entendido. Me quedaré en silencio hasta que me digas despierta."
            )
            self.state = RobotStates.SILENCIO
            self._set_web_status("SILENCIOSA")
            return

        # ====================================================
        # APAGAR: solo con la orden completa y confirmación
        # ====================================================

        # Despedirse no apaga a Yura: queda en silencio hasta que la llamen.

        if texto_util.pide_orden(
            comando, ("salir", "terminar", "adios", "hasta luego", "chau")
        ):

            self.hw.hablar(
                "Hasta luego. Tupananchiskama. "
                "Dime despierta cuando quieras volver."
            )

            self.state = RobotStates.SILENCIO
            self._set_web_status("SILENCIOSA")

            return

        # ====================================================
        # TRADUCIR
        # ====================================================

        if texto_util.pide_orden(
            comando, ("traducir", "traductor", "traduccion")
        ):

            conversacion.cancelar_sesion_educativa()
            self.state = RobotStates.TRADUCIR

            self.hw.hablar(
                "Modo traductor. "
                "Dime una palabra o frase en español "
                "y te diré cómo se dice en quechua."
            )

            return

        # ====================================================
        # CONVERSAR
        # ====================================================

        if texto_util.pide_orden(
            comando, ("conversar", "conversemos", "hablemos")
        ):

            conversacion.cancelar_sesion_educativa()
            self.state = RobotStates.CONVERSAR

            self.hw.hablar(
                "Modo conversación activado. "
                "¿De qué te gustaría hablar hoy?"
            )

            return

        # ====================================================
        # JUGAR
        # ====================================================

        if texto_util.pide_orden(comando, ("jugar", "juguemos", "juego")):

            self.state = RobotStates.JUEGO
            self.juego.reiniciar()

            return

        # ====================================================
        # OPCIÓN DESCONOCIDA
        # ====================================================

        resultado = conversacion.procesar_entrada(
            opcion,
            self.groq_client
        )

        if resultado["accion"] == "menu":
            self.state = RobotStates.MENU
            self.hw.hablar(resultado["respuesta"])
            return

        self.state = RobotStates.CONVERSAR
        self._responder_conversacion(resultado)

    def _responder_conversacion(self, resultado):
        """Dice la respuesta y, si enseña una palabra, la fija en pantalla."""
        pantalla = resultado.get("pantalla")
        if pantalla:
            self._set_web_status(
                "PENSANDO",
                content=pantalla.get("content", ""),
                translation=pantalla.get("translation", ""),
                fijar=True
            )
        self.hw.hablar(resultado["respuesta"])
        self._reproducir_pronunciacion(resultado.get("pronunciar"))

    def _reproducir_pronunciacion(self, quechua):
        """Si la docente grabó esta palabra, se escucha su voz después de
        la de Yura (la voz sintética no pronuncia bien el quechua)."""
        ruta = pronunciaciones.audio_de(quechua) if quechua else None
        if ruta:
            self.hw.reproducir_grabacion(ruta)

    # ========================================================
    # MODO DOCENTE
    # ========================================================

    def _docente_pedido(self):
        pedido = getattr(self, "pedido_docente", None)
        return pedido is not None and pedido.is_set()

    def _revisar_pedido_docente(self):
        if self._docente_pedido() and self.state != RobotStates.ENSENAR:
            raise ModoDocentePedido()

    def activar_modo_docente(self):
        """Lo llama la página web (otro hilo)."""
        self.ultima_actividad_docente = time.monotonic()
        self.pedido_docente.set()
        if self.state != RobotStates.ENSENAR:
            self.audio_manager.cancelar.set()

    def terminar_modo_docente(self):
        self.pedido_docente.clear()
        self.ordenes_docente.put(("salir", None))

    def pedir_grabacion_docente(self, palabra):
        if self.state != RobotStates.ENSENAR:
            return False
        self.ultima_actividad_docente = time.monotonic()
        self.ensenanza = {"estado": "esperando", "palabra": palabra}
        self.ordenes_docente.put(("grabar", palabra))
        return True

    def _entrar_modo_docente(self):
        self.audio_manager.cancelar.clear()
        conversacion.cancelar_sesion_educativa()
        self.state = RobotStates.ENSENAR
        self.ultima_actividad_docente = time.monotonic()
        self.ensenanza = {"estado": "listo_para_grabar"}
        while not self.ordenes_docente.empty():
            self.ordenes_docente.get_nowait()
        self._set_web_status("ESPERANDO", content="Modo docente", translation="Elige una palabra y presiona Grabar.")
        self.hw.hablar("Modo docente. Elige una palabra y presiona grabar.")

    def _salir_modo_docente(self, motivo="Modo docente terminado."):
        self.pedido_docente.clear()
        pronunciaciones.descartar_pendiente()
        self.ensenanza = {"estado": "inactivo"}
        self.state = RobotStates.MENU
        self._set_web_status("ESPERANDO", content=conversacion.PRESENTACION_YURA, translation="")
        self.hw.hablar(motivo + " Volvemos al menú principal.")

    def ejecutar_ensenar(self):
        try:
            orden, palabra = self.ordenes_docente.get(timeout=0.5)
        except queue.Empty:
            if time.monotonic() - self.ultima_actividad_docente > 15 * 60:
                # Si la docente se olvida de terminar, Yura no queda muda.
                self._salir_modo_docente("Pasaron 15 minutos sin grabar; cierro el modo docente.")
            return

        if orden == "salir":
            self._salir_modo_docente()
        elif orden == "grabar":
            self._grabar_para_docente(palabra)

    def _grabar_para_docente(self, palabra):
        pronunciaciones.descartar_pendiente()
        self.ensenanza = {"estado": "grabando", "palabra": palabra}
        self._set_web_status("ESCUCHANDO", content=palabra["quechua"], translation=palabra["espanol"])
        # Mismas pistas que en una actividad, para anotar cómo escribe el
        # reconocedor la palabra bien dicha.
        pistas = [palabra["quechua"]] + list(texto_util.PISTAS_GENERALES)
        escuchado = self.escuchar_voz(
            solo_local=True, pistas=pistas, guardar_audio_en=pronunciaciones.ruta_pendiente()
        )
        self.ultima_actividad_docente = time.monotonic()

        if not os.path.exists(pronunciaciones.ruta_pendiente()):
            self.ensenanza = {"estado": "sin_voz", "palabra": palabra}
            self._set_web_status("ESPERANDO", content=palabra["quechua"], translation="No escuché nada. Graba otra vez.")
            return

        self.ensenanza = {
            "estado": "grabado",
            "palabra": palabra,
            "transcripcion": escuchado,
            "reconocida": texto_util.respuesta_quechua_correcta(escuchado, palabra["quechua"]),
            "confunde_con": pronunciaciones.otra_palabra_igual(escuchado, palabra["quechua"]) if escuchado else None,
        }
        self._set_web_status(
            "ESPERANDO",
            content=palabra["quechua"],
            translation=f"Escuché: {escuchado}" if escuchado else "Grabé la voz, pero no entendí palabras.",
            fijar=True,
        )

    def _escuchar_con_ordenes(self, solo_local=False, pistas=None):
        """Escucha y atiende "apágate" en cualquier modo (antes solo en el
        menú: en conversación la orden se enviaba a Groq)."""
        texto = self.escuchar_voz(solo_local=solo_local, pistas=pistas)
        if texto_util.es_orden_apagar(self._normalizar_texto(texto)):
            self._confirmar_apagado()
            return ""
        return texto

    def _confirmar_apagado(self):
        self.hw.hablar(
            "¿Seguro que quieres que me apague? Di sí para confirmar."
        )
        respuesta = self._normalizar_texto(self.escuchar_voz())

        # Si no se entendió ni sí ni no (silencio o ruido), se pregunta una
        # vez más en lugar de quedarse encendida sin avisar.
        if not texto_util.es_afirmacion(respuesta) and not texto_util.es_negacion(respuesta):
            self.hw.hablar("No te entendí. ¿Me apago? Di sí o no.")
            respuesta = self._normalizar_texto(self.escuchar_voz())

        if texto_util.es_afirmacion(respuesta):
            self.hw.hablar(
                "Hasta luego. Tupananchiskama. Me voy a apagar."
            )
            self.state = RobotStates.SALIR
            self.running = False
            # Por ahora solo se cierra la aplicación; con YURA_APAGAR_EQUIPO=1
            # también se apaga la computadora.
            self.apagar_equipo = (
                os.environ.get("YURA_APAGAR_EQUIPO", "0").strip() == "1"
            )
            raise ApagadoConfirmado()

        self.hw.hablar("De acuerdo, sigo encendida.")

    def apagar_equipo_si_corresponde(self):
        """Apaga la computadora cuando se confirmó "apágate" por voz.

        Solo si está activado con YURA_APAGAR_EQUIPO=1 (por defecto no).
        """
        if not getattr(self, "apagar_equipo", False):
            return
        print("[SISTEMA]: Apagando la computadora...")
        try:
            subprocess.run(["systemctl", "poweroff"], timeout=15, check=False)
        except Exception as exc:
            print(f"[SISTEMA]: No se pudo apagar la computadora: {exc}")

    def ejecutar_silencio(self):
        # Privacidad: en silencio Yura solo espera "despierta"; lo que se
        # habla en el aula se transcribe en esta computadora y no sale a internet.
        entrada = self._escuchar_con_ordenes(solo_local=True)
        entrada = self._normalizar_texto(entrada)
        entrada = re.sub(r"^yura\s+", "", entrada).strip()

        # "silencio" ya no despierta a Yura: "guarda silencio" la despertaba.
        if texto_util.pide_orden(
            entrada,
            (
                "puedes hablar",
                "puede hablar",
                "despierta",
                "despiertate",
                "vuelve",
                "volver",
            )
        ):
            self.state = RobotStates.MENU
            self._set_web_status("ESPERANDO")
            self.hw.hablar(
                "Ya estoy de vuelta. ¿Qué te gustaría hacer?"
            )
            return

        self._set_web_status("SILENCIOSA")

    # ========================================================
    # EJECUTAR JUEGO
    # ========================================================

    def ejecutar_juego(self):
        resultado = self.juego.ejecutar_turno()

        if resultado == "menu":
            self.state = RobotStates.MENU

    # ========================================================
    # EJECUTAR TRADUCTOR
    # ========================================================

    def ejecutar_traducir(self):
        resultado = traductor.ejecutar_traducir(
            self._escuchar_con_ordenes,
            self.hw.hablar,
            self.db_conn,
            self.groq_client,
            lambda: self.running and self.state == RobotStates.TRADUCIR,
            on_status=self._set_web_status,
        )

        if resultado == "menu":
            self.state = RobotStates.MENU

    # ========================================================
    # EJECUTAR CONVERSACIÓN
    # ========================================================

    def ejecutar_conversar(self):

        if not self.saludo_inicial_done:
            self.saludo_inicial_done = True

        # En una práctica, el reconocedor recibe la palabra a repetir como pista.
        entrada = self._escuchar_con_ordenes(pistas=conversacion.pistas_practica())
        if not entrada:
            self._set_web_status("ESPERANDO", content="Es hora de practicar quechua.", translation="")
            return

        self._set_web_status("PENSANDO")
        resultado = conversacion.procesar_entrada(
            entrada,
            self.groq_client,
            self.historial_conversacion
        )

        if resultado["accion"] == "menu":
            # Volver al menú; apagar solo con la orden "apagar" del menú.
            conversacion.cancelar_sesion_educativa()
            self.state = RobotStates.MENU

        self._responder_conversacion(resultado)

    # ========================================================
    # LOOP PRINCIPAL
    # ========================================================

    def loop_principal(self):

        print(
            "\n[SISTEMA]: "
            "Yura operativo de forma local e independiente..."
        )

        self.fallo_fatal = False
        errores_seguidos = 0

        try:

            while self.running:
                depuracion.depurar(
                    f"[DEBUG AUDIO] reiniciando escucha state={self.state}"
                )

                # Un error en un modo (p. ej. "database is locked") ya no
                # mata el hilo en silencio: se avisa y se vuelve al menú.
                try:
                    self._ejecutar_estado_actual()
                    errores_seguidos = 0
                except ApagadoConfirmado:
                    break
                except ModoDocentePedido:
                    self._entrar_modo_docente()
                    errores_seguidos = 0
                except Exception as exc:
                    errores_seguidos += 1
                    print(f"[ERROR SISTEMA]: {type(exc).__name__}: {exc}")
                    traceback.print_exc()
                    if errores_seguidos >= 5:
                        print("[ERROR SISTEMA]: Demasiados errores seguidos; Yura se detiene.")
                        self.fallo_fatal = True
                        self.running = False
                        self._set_web_status("SIN_CONEXION", content="", translation="")
                        break
                    self.state = RobotStates.MENU
                    self._set_web_status(
                        "ESPERANDO",
                        content="Tuve un problema. Volvamos al menú.",
                        translation=""
                    )
                    time.sleep(1)

        except KeyboardInterrupt:

            print(
                "\n[SISTEMA]: "
                "Apagando a Yura de forma segura..."
            )

        finally:

            if self.db_conn:

                try:
                    self.db_conn.close()
                except Exception:
                    pass

    def _ejecutar_estado_actual(self):

        if self.state == RobotStates.ENSENAR and not self._docente_pedido():
            # Se presionó "Terminar" mientras grababa.
            self._salir_modo_docente()
            return
        if self._docente_pedido() and self.state != RobotStates.ENSENAR:
            self._entrar_modo_docente()
            return

        # --------------------------------------------
        # MENÚ
        # --------------------------------------------

        if self.state == RobotStates.MENU:

            self.ejecutar_menu()

        # --------------------------------------------
        # JUEGO
        # --------------------------------------------

        elif self.state == RobotStates.JUEGO:

            self.ejecutar_juego()

        # --------------------------------------------
        # CONVERSACIÓN
        # --------------------------------------------

        elif self.state == RobotStates.CONVERSAR:

            self.ejecutar_conversar()

        # --------------------------------------------
        # TRADUCTOR
        # --------------------------------------------

        elif self.state == RobotStates.TRADUCIR:

            self.ejecutar_traducir()

        # --------------------------------------------
        # SILENCIO CONTROLADO
        # --------------------------------------------

        elif self.state == RobotStates.SILENCIO:

            self.ejecutar_silencio()

        # --------------------------------------------
        # MODO DOCENTE (enseñar pronunciaciones)
        # --------------------------------------------

        elif self.state == RobotStates.ENSENAR:

            self.ejecutar_ensenar()

        # --------------------------------------------
        # SALIR
        # --------------------------------------------

        elif self.state == RobotStates.SALIR:

            self.running = False


# ============================================================
# ARRANQUE
# ============================================================

if __name__ == "__main__":

    cerebro = BrainYura()
    cerebro.loop_principal()
    cerebro.apagar_equipo_si_corresponde()
