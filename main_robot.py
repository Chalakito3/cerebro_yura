#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
import sqlite3
import shutil
import threading
from datetime import datetime, timezone
import traductor
import subprocess
import ctypes
import wave
import time
import tempfile
import whisper
import vosk
from groq import Groq
import conversacion
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
# ESTADOS DEL ROBOT
# ============================================================

class RobotStates:
    MENU = "MENU"
    CONVERSAR = "CONVERSAR"
    JUEGO = "JUEGO"
    TRADUCIR = "TRADUCIR"
    SILENCIO = "SILENCIO"
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
        self.voz_mujer = "es-MX-DaliaNeural"
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
            r"^En quechua (?:se dice|se puede decir)\s*:??\s*(.+)$",
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

                res = None
                for intento in range(2):
                    res = subprocess.run(
                        cmd_tts,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
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
                        stderr=subprocess.DEVNULL
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
                            stderr=subprocess.DEVNULL
                        )
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
                    stderr=subprocess.DEVNULL
                )
                if resultado.returncode != 0:
                    print("[AUDIO] Speech Dispatcher no pudo reproducir la voz.")
            else:
                espeak = shutil.which("espeak")
                if espeak:
                    subprocess.run(
                        [espeak, "-v", "es-la", "-s", "140", texto_voz],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
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

    def mover_actuador(self, comando):
        print(f"[FISICO]: Motores ejecutando -> {comando}")


# ============================================================
# CEREBRO DE YURA
# ============================================================

class BrainYura:

    def __init__(self):

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

        self.audio_manager = AudioManager()
        self.hw = HardwareInterface(
            self.audio_manager,
            on_status=self._set_web_status
        )
        whisper_name = os.environ.get("YURA_WHISPER_MODEL", "base").strip() or "base"
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
        # RECONOCEDOR DE VOZ
        # ----------------------------------------------------

        self.vosk_model = self._cargar_modelo_vosk()
        self.vosk_recognizer = None

        if self.vosk_model is not None:
            try:
                self.vosk_recognizer = vosk.KaldiRecognizer(
                    self.vosk_model,
                    16000
                )
            except Exception as exc:
                print(f"[ERROR VOSK]: No se pudo crear el recognizer: {exc}")
                self.vosk_recognizer = None

        self._buscar_headset_usb()

        # ----------------------------------------------------
        # SISTEMAS LOCALES
        # ----------------------------------------------------

        self.inicializar_sistemas_locales()
        self.juego = Juego(
            ["gato", "perro", "sol", "agua", "casa", "arbol"],
            lambda palabra: traductor.consultar_diccionario_local(
                palabra,
                self.db_conn
            ),
            self.escuchar_voz,
            self.hw.hablar,
            self._mover_actuador,
            self._normalizar_texto,
            self._set_game_event
        )

    def _set_web_status(
        self,
        phase,
        content=None,
        translation=None,
        result=None
    ):
        with self.web_status_lock:
            self.web_status["phase"] = phase
            if content is not None:
                self.web_status["content"] = str(content).strip()
            if translation is not None:
                self.web_status["translation"] = str(translation).strip()
            if result is not None:
                self.web_status["result"] = result
            self.web_status["updated_at"] = datetime.now(timezone.utc).isoformat()

    def get_web_status(self):
        with self.web_status_lock:
            return dict(self.web_status)

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
            self._set_web_status(
                "CELEBRANDO" if data.get("correct") else "TRISTE",
                content=data.get("question", ""),
                translation=data.get("answer", ""),
                result="CORRECTO" if data.get("correct") else "INCORRECTO"
            )

    # ========================================================
    # CARGAR MODELO VOSK
    # ========================================================

    def _cargar_modelo_vosk(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        rutas = [
            os.path.join(base_dir, "model"),
            os.path.join(base_dir, "vosk-model-es")
        ]

        for ruta in rutas:
            if not os.path.isdir(ruta):
                continue

            try:
                modelo = vosk.Model(ruta)
                print(f"[VOSK]: Modelo cargado desde '{ruta}'")
                return modelo
            except Exception as exc:
                print(f"[ERROR VOSK]: Falló al cargar '{ruta}': {exc}")

        print("[ALERTA VOSK]: No se encontró un modelo Vosk válido.")
        return None

    # ========================================================
    # BUSCAR HEADSET USB
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

        api_key = os.environ.get("GROQ_API_KEY", "").strip()
        if api_key:
            return api_key

        candidatos = []
        base_dir = os.path.dirname(os.path.abspath(__file__))
        home_dir = os.path.expanduser("~")

        candidatos.extend([
            os.path.join(base_dir, ".env"),
            os.path.join(home_dir, ".env"),
            os.path.join(base_dir, ".env.local"),
            os.path.join(home_dir, ".bashrc"),
            os.path.join(home_dir, ".profile"),
            os.path.join(home_dir, ".zshrc")
        ])

        for ruta in candidatos:
            if not os.path.exists(ruta):
                continue
            try:
                with open(ruta, "r", encoding="utf-8", errors="ignore") as fh:
                    for linea in fh:
                        texto = linea.strip()
                        if not texto or texto.startswith("#"):
                            continue
                        if "GROQ_API_KEY" not in texto:
                            continue
                        for pref in ("export ", ""):
                            if texto.startswith(pref):
                                parte = texto[len(pref):].strip()
                                if "=" in parte:
                                    clave, valor = parte.split("=", 1)
                                    clave = clave.strip()
                                    valor = valor.strip().strip("\"'")
                                    if clave == "GROQ_API_KEY" and valor:
                                        return valor
                        if "=" in texto:
                            clave, valor = texto.split("=", 1)
                            clave = clave.strip()
                            valor = valor.strip().strip("\"'")
                            if clave == "GROQ_API_KEY" and valor:
                                return valor
            except Exception:
                continue

        for comando in (
            "bash -lc 'source ~/.bashrc >/dev/null 2>&1 || true; source ~/.profile >/dev/null 2>&1 || true; printf %s \"${GROQ_API_KEY:-}\"'",
            "bash -lc 'printf %s \"${GROQ_API_KEY:-}\"'",
            "zsh -lc 'source ~/.zshrc >/dev/null 2>&1 || true; printf %s \"${GROQ_API_KEY:-}\"'"
        ):
            try:
                resultado = subprocess.run(
                    comando,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False
                )
                valor = resultado.stdout.strip()
                if valor:
                    return valor
            except Exception:
                continue

        return ""

    def _crear_cliente_groq(self):

        api_key = self._obtener_api_key_groq()

        if not api_key:
            print(
                "[ALERTA GROQ]: "
                "GROQ_API_KEY no está disponible en el entorno del proceso ni en los perfiles/.env del proyecto. "
                "El fallback online queda deshabilitado."
            )
            return None

        try:
            os.environ["GROQ_API_KEY"] = api_key
            cliente = Groq(api_key=api_key)
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

        if texto is None:
            return ""

        try:
            texto = str(texto).strip()
        except Exception:
            return ""

        if texto == "":
            return ""

        texto = texto.lower()

        texto = (
            texto
            .replace("á", "a")
            .replace("é", "e")
            .replace("í", "i")
            .replace("ó", "o")
            .replace("ú", "u")
            .replace("ü", "u")
        )

        texto = re.sub(
            r"[^a-z0-9\s]",
            " ",
            texto
        )

        texto = re.sub(
            r"\s+",
            " ",
            texto
        )

        return texto.strip()

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

    def escuchar_voz(self):

        self._set_web_status("ESCUCHANDO")
        print(
            f"[DEBUG AUDIO] iniciando escucha state={self.state} "
            f"device={self.audio_manager.input_device} "
            f"device_index={self.dispositivo_index}"
        )

        if self.dispositivo_index is None:
            print("[AUDIO] Índice inicial no disponible; AudioManager reenumerará el JACK.")

        print("\n==============================")
        print("[YURA ESCUCHA]")
        print(f"[MICRÓFONO]: índice {self.dispositivo_index}")
        print("[WHISPER]: reconocimiento principal")
        print("==============================")

        try:
            time.sleep(0.3)
            print(
                "[DEBUG AUDIO] captura iniciada "
                f"device={self.audio_manager.input_device}"
            )
            print("[DEBUG AUDIO] antes de esperar audio")
            audio_bytes = self.audio_manager.grabar_hasta_silencio(
                espera_maxima=10.0,
                duracion_maxima=15.0,
                silencio_final=1.0,
                bloque_ms=80
            )
            print("[DEBUG AUDIO] después de recibir audio")
            print("[DEBUG AUDIO] captura finalizada")
            print(
                "[DEBUG AUDIO] audio recibido: "
                f"{0 if audio_bytes is None else len(audio_bytes)} bytes"
            )

        except Exception as exc:
            print(f"[ERROR MICROFONO]: {exc}")
            print(f"[DEBUG AUDIO] excepción durante captura: {type(exc).__name__}")
            self._set_web_status("ESPERANDO")
            return ""

        if not audio_bytes:
            self.dispositivo_index = self.audio_manager.input_device
            print("[YURA]: No se capturó audio.")
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

            texto_gemini = self.gemini_transcriber.transcribir(audio_path)
            if texto_gemini:
                motor_transcripcion = "Gemini"
                texto = self._normalizar_texto(texto_gemini)
                print(f"[GEMINI ESCUCHÓ]: {texto}")
            elif self.whisper_model is not None:
                motor_transcripcion = "Whisper"
                print("[WHISPER]: Fallback de precisión activado.")
                print("[DEBUG AUDIO] enviando audio a Whisper")
                inicio_whisper = time.perf_counter()
                resultado = self.whisper_model.transcribe(
                    audio_path,
                    language="es",
                    initial_prompt=(
                        "Español boliviano con algunas palabras en quechua. "
                        "Conversación entre un estudiante y un robot educativo. "
                        "Comandos posibles: preséntate, conversar, jugar, traducir, "
                        "enséñame quechua, practicar, silencio y salir. "
                        "Vocabulario quechua: rimaykullayki, imaynalla kachkanki, "
                        "allin p'unchay, yusulpayki, anchata munakuyki, ari, mana, "
                        "yaku, wasi y puka. Transcribe solo lo que escuchas."
                    ),
                    fp16=False,
                    temperature=0,
                    beam_size=5,
                    best_of=1,
                    without_timestamps=True,
                    condition_on_previous_text=False
                )
                print("[DEBUG AUDIO] Whisper respondió")
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
            print(f"[DEBUG AUDIO] excepción durante Whisper: {type(exc).__name__}")
            texto = ""
        finally:
            try:
                if os.path.exists(audio_path):
                    os.remove(audio_path)
            except Exception:
                pass

        if texto == "":
            print("[YURA]: No logré escuchar ninguna palabra.")
            print("[DEBUG AUDIO] Whisper no produjo texto")
            self._set_web_status("ESPERANDO")
            return ""

        print(f"[TRANSCRIPCIÓN FINAL - {motor_transcripcion}]: {texto}")
        print("[DEBUG AUDIO] texto listo; devolviendo al estado actual")
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

        opcion = self.escuchar_voz()

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

        if (
            "presentate" in comando
            or "presentarte" in comando
            or "quien eres" in comando
        ):
            self.hw.hablar(
                conversacion.PRESENTACION_YURA
            )
            self.state = RobotStates.MENU
            return

        if (
            "silencio" in comando
            or "guarda silencio" in comando
            or "guardar silencio" in comando
            or "quedate en silencio" in comando
            or "silenciate" in comando
            or "callate" in comando
            or "cállate" in comando
            or comando == "espera"
            or comando.startswith("espera ")
        ):
            self.hw.hablar(
                "Entendido. Me quedaré en silencio hasta que me pidas volver."
            )
            self.state = RobotStates.SILENCIO
            self._set_web_status("SILENCIOSA")
            return

        # ====================================================
        # SALIR LIMPIO DESDE EL MENÚ
        # ====================================================

        if any(
            frase in opcion for frase in (
                "salir",
                "apagar",
                "terminar",
                "adios"
            )
        ):

            self.hw.hablar(
                "Hasta luego."
            )

            self.state = RobotStates.SALIR
            self.running = False

            return

        # ====================================================
        # TRADUCIR
        # ====================================================

        if (
            "traducir" in opcion
            or "traductor" in opcion
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

        if "conversar" in opcion:

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

        if "jugar" in opcion:

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
        self.hw.hablar(resultado["respuesta"])

    def ejecutar_silencio(self):
        entrada = self.escuchar_voz()
        entrada = self._normalizar_texto(entrada)
        entrada = re.sub(r"^yura\s+", "", entrada).strip()

        if any(
            frase in entrada for frase in (
                "puedes hablar",
                "puede hablar",
                "despierta",
                "vuelve",
                "volver",
                "silencio",
                "guarda silencio",
                "guardar silencio"
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
            self.escuchar_voz,
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

        entrada = self.escuchar_voz()
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
            self.state = RobotStates.SALIR
            self.running = False

        self.hw.hablar(resultado["respuesta"])

    # ========================================================
    # LOOP PRINCIPAL
    # ========================================================

    def loop_principal(self):

        print(
            "\n[SISTEMA]: "
            "Yura operativo de forma local e independiente..."
        )

        try:

            while self.running:
                print(
                    f"[DEBUG AUDIO] reiniciando escucha state={self.state}"
                )

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
                # SALIR
                # --------------------------------------------

                elif self.state == RobotStates.SALIR:

                    self.running = False

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


# ============================================================
# ARRANQUE
# ============================================================

if __name__ == "__main__":

    cerebro = BrainYura()

    cerebro.loop_principal()