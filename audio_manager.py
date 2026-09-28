import numpy as np
import math
import os
import re
import subprocess
import threading
from collections import deque
import sounddevice as sd
import depuracion


class AudioManager:

    @staticmethod
    def _calcular_nivel_audio(bloque):
        bloque = np.asarray(bloque, dtype=np.float32)
        if bloque.size == 0:
            return 0.0
        return float(np.mean(np.abs(bloque)))

    @staticmethod
    def _calcular_umbral_ruido(nivel_ruido):
        nivel_ruido = float(nivel_ruido or 0.0)
        nivel_ruido = max(0.0005, min(nivel_ruido, 0.0800))
        return max(0.0060, min(0.1200, nivel_ruido * 1.25 + 0.0040))

    def _ruido_para_umbral(self, nivel_ruido):
        """Nivel de ruido a usar y si la calibración parece contener voz.

        Si se mide mucho más ruido que el normal de la sala, es que la
        persona ya estaba hablando: antes eso subía el umbral hasta 17 veces
        y la respuesta ("sí") se perdía.
        """
        nivel_ruido = float(nivel_ruido or 0.0)
        referencia = self.ruido_referencia

        if referencia is None:
            if nivel_ruido > 0.03:
                return 0.002, True
            self.ruido_referencia = nivel_ruido
            return nivel_ruido, False

        if nivel_ruido > max(0.01, referencia * 4):
            return referencia, True

        self.ruido_referencia = referencia * 0.8 + nivel_ruido * 0.2
        return nivel_ruido, False

    @staticmethod
    def _bloques_minimos_inicio_voz(bloque_ms):
        duracion_bloque = max(0.01, float(bloque_ms) / 1000.0)
        return max(1, math.ceil(0.24 / duracion_bloque))

    def __init__(self, sample_rate=16000, channels=1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.input_device = None
        self.output_device = None
        self.output_alsa_device = None
        self.input_sample_rate = sample_rate
        self.input_channels = channels
        self.input_candidates = []
        # Ruido normal de la sala, aprendido en calibraciones anteriores.
        self.ruido_referencia = None
        # Al activar el modo docente se corta la escucha en curso.
        self.cancelar = threading.Event()

        print("[AUDIO] Buscando dispositivos...")
        self.detectar_dispositivos()
        self.seleccionar_entrada()
        self.seleccionar_salida()

    @staticmethod
    def _normalizar_nombre_dispositivo(nombre):
        if nombre is None:
            return ""
        texto = str(nombre).lower()
        texto = texto.replace("_", " ")
        texto = re.sub(r"[^a-z0-9]+", " ", texto)
        return " ".join(texto.split())

    @staticmethod
    def _es_virtual(nombre):
        nombre = nombre.lower()
        return any(
            palabra in nombre
            for palabra in (
                "monitor",
                "loopback",
                "dummy",
                "null",
                "virtual"
            )
        )

    @classmethod
    def _obtener_dispositivo_entrada_activo(cls):
        intentos = [
            ["wpctl", "inspect", "@DEFAULT_AUDIO_SOURCE@"],
            ["pactl", "get-default-source"],
            ["pacmd", "list-sources"],
        ]

        for comando in intentos:
            try:
                resultado = subprocess.run(
                    comando,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=2
                )
            except (OSError, subprocess.SubprocessError):
                continue

            if resultado.returncode != 0:
                continue

            salida = (resultado.stdout or "") + "\n" + (resultado.stderr or "")
            if not salida.strip():
                continue

            if comando[0] == "wpctl":
                for linea in salida.splitlines():
                    if "node.name" in linea or "node.nick" in linea or "alsa.card_name" in linea:
                        try:
                            _, _, valor = linea.partition("=")
                            valor = valor.strip().strip('"')
                            if valor:
                                return valor
                        except Exception:
                            continue
            elif comando[0] == "pactl":
                valor = salida.strip()
                if valor:
                    return valor
            elif comando[0] == "pacmd":
                for linea in salida.splitlines():
                    if "name:" in linea and "alsa_input" in linea.lower():
                        valor = linea.split(":", 1)[1].strip().strip('"')
                        if valor:
                            return valor

        return None

    @classmethod
    def _reordenar_candidatos_por_dispositivo_activo(cls, candidatos, nombre_activo=None):
        if not candidatos:
            return candidatos

        nombre_activo = nombre_activo or cls._obtener_dispositivo_entrada_activo()
        if not nombre_activo:
            return list(candidatos)

        nombre_activo_norm = cls._normalizar_nombre_dispositivo(nombre_activo)
        tokens_activos = {
            token for token in nombre_activo_norm.split() if len(token) >= 3
        }

        def _puntuacion(candidato):
            nombre = cls._normalizar_nombre_dispositivo(candidato["name"])
            if not nombre:
                return -1
            if nombre_activo_norm == nombre:
                return 1000
            if nombre_activo_norm in nombre or nombre in nombre_activo_norm:
                return 800

            puntuacion = 0
            puntuacion += sum(
                30 for token in tokens_activos if token in nombre
            )
            if any(token in nombre for token in ("usb", "headset", "bluetooth", "microfono", "mic", "input")):
                puntuacion += 25
            if any(token in nombre for token in ("analog", "stereo", "built", "internal")):
                puntuacion -= 25
            if any(token in nombre for token in ("monitor", "loopback", "virtual", "dummy")):
                puntuacion -= 100

            return max(0, puntuacion)

        candidatos_ordenados = sorted(
            candidatos,
            key=lambda candidato: _puntuacion(candidato),
            reverse=True
        )
        return candidatos_ordenados

    @staticmethod
    def _prioridad_entrada(dispositivo):
        nombre = str(dispositivo["name"]).lower()
        prioridad = 0

        if "usb" in nombre or "headset" in nombre or "logitech" in nombre:
            prioridad += 100
        if "hw:0,0" in nombre:
            prioridad += 20
        if "alc662" in nombre or "hda intel pch" in nombre:
            prioridad += 10
        if "pipewire" in nombre or "default" in nombre:
            prioridad += 10
        if AudioManager._es_virtual(nombre):
            prioridad -= 100

        return prioridad

    @staticmethod
    def _prioridad_salida(dispositivo):
        nombre = str(dispositivo["name"]).lower()
        prioridad = 0

        if "usb" in nombre or "headset" in nombre:
            prioridad += 70
        if "speaker" in nombre or "analog" in nombre:
            prioridad += 30
        if "output" in nombre:
            prioridad += 20
        if AudioManager._es_virtual(nombre):
            prioridad -= 100

        return prioridad

    def detectar_dispositivos(self):
        self.input_candidates = []
        try:
            dispositivos = sd.query_devices()
        except Exception as exc:
            print(f"[AUDIO] No se pudieron listar dispositivos: {exc}")
            return

        for indice, dispositivo in enumerate(dispositivos):
            nombre = str(dispositivo.get("name", "Desconocido"))
            entradas = int(dispositivo.get("max_input_channels", 0) or 0)
            salidas = int(dispositivo.get("max_output_channels", 0) or 0)
            depuracion.depurar(
                f"[AUDIO] Dispositivo {indice}: {nombre} "
                f"(entrada={entradas}, salida={salidas})"
            )

            if entradas > 0 and not self._es_virtual(nombre):
                self.input_candidates.append({
                    "index": indice,
                    "name": nombre,
                    "info": dispositivo,
                    "priority": self._prioridad_entrada(dispositivo)
                })

        self.input_candidates.sort(
            key=lambda candidato: candidato["priority"],
            reverse=True
        )

    def validar_entrada(self, candidato):
        indice = candidato["index"]
        info = candidato["info"]
        frecuencia = 48000
        canales_disponibles = int(info.get("max_input_channels", 1) or 1)
        canales = min(2, max(1, canales_disponibles))

        try:
            sd.check_input_settings(
                device=indice,
                channels=canales,
                dtype="float32",
                samplerate=frecuencia
            )
            with sd.InputStream(
                device=indice,
                channels=canales,
                dtype="float32",
                samplerate=frecuencia
            ):
                pass
            return frecuencia, canales
        except Exception:
            return None, None

    def seleccionar_entrada(self):
        self.input_device = None
        self.input_sample_rate = self.sample_rate
        self.input_channels = self.channels
        candidatos = list(self.input_candidates)
        indice_configurado = os.environ.get("YURA_INPUT_DEVICE", "").strip()

        if not indice_configurado:
            candidatos = self._reordenar_candidatos_por_dispositivo_activo(candidatos)

        if indice_configurado.lower() in {"pipewire", "pw"}:
            candidatos.sort(
                key=lambda candidato: str(candidato["name"]).lower() != "pipewire"
            )
        elif indice_configurado.isdigit():
            indice_configurado = int(indice_configurado)
            candidatos.sort(
                key=lambda candidato: candidato["index"] != indice_configurado
            )
        elif indice_configurado:
            configurado = indice_configurado.casefold()
            candidatos.sort(
                key=lambda candidato: configurado not in str(candidato["name"]).casefold()
            )

        for candidato in candidatos:
            frecuencia, canales = self.validar_entrada(candidato)
            if frecuencia is None:
                depuracion.depurar(
                    f"[AUDIO] Dispositivo {candidato['name']} no disponible. "
                    "Probando siguiente dispositivo..."
                )
                continue

            self.input_device = candidato["index"]
            self.input_sample_rate = frecuencia
            self.input_channels = canales
            depuracion.depurar(
                f"[AUDIO] Entrada seleccionada: {candidato['name']} "
                f"({canales} canal(es), {frecuencia} Hz)"
            )
            return

        print("[AUDIO] No se encontró una entrada de audio compatible.")

    def seleccionar_salida(self):
        try:
            dispositivos = sd.query_devices()
        except Exception:
            dispositivos = []

        candidatos = []
        for indice, dispositivo in enumerate(dispositivos):
            if int(dispositivo.get("max_output_channels", 0) or 0) <= 0:
                continue
            candidatos.append({
                "index": indice,
                "name": str(dispositivo.get("name", "Desconocido")),
                "info": dispositivo,
                "priority": self._prioridad_salida(dispositivo)
            })

        candidatos.sort(
            key=lambda candidato: candidato["priority"],
            reverse=True
        )

        indice_configurado = os.environ.get("YURA_OUTPUT_DEVICE", "").strip()
        if indice_configurado.isdigit():
            indice_configurado = int(indice_configurado)
            candidatos.sort(
                key=lambda candidato: candidato["index"] != indice_configurado
            )
        elif indice_configurado:
            configurado = indice_configurado.casefold()
            candidatos.sort(
                key=lambda candidato: configurado not in str(candidato["name"]).casefold()
            )

        for candidato in candidatos:
            try:
                frecuencia = int(
                    round(float(candidato["info"].get("default_samplerate", 0) or 0))
                )
                if frecuencia <= 0:
                    frecuencia = 44100
                sd.check_output_settings(
                    device=candidato["index"],
                    channels=1,
                    dtype="float32",
                    samplerate=frecuencia
                )
                with sd.OutputStream(
                    device=candidato["index"],
                    channels=1,
                    dtype="float32",
                    samplerate=frecuencia
                ):
                    pass
                self.output_device = candidato["index"]
                coincidencia = re.search(
                    r"\((hw:\d+(?:,\d+)?)\)",
                    candidato["name"]
                )
                if coincidencia:
                    self.output_alsa_device = coincidencia.group(1)
                print(f"[AUDIO] Salida seleccionada: {candidato['name']}")
                return
            except Exception:
                print(
                    f"[AUDIO] Salida {candidato['name']} no disponible. "
                    "Probando siguiente dispositivo..."
                )

        print("[AUDIO] No se encontró una salida de audio validada.")


    def grabar_hasta_silencio(
        self,
        espera_maxima=10.0,
        duracion_maxima=15.0,
        silencio_final=1.0,
        bloque_ms=80
    ):
        """Graba una respuesta completa usando actividad de voz y silencio."""
        self.detectar_dispositivos()
        self.seleccionar_entrada()

        if self.input_device is None or not self.input_candidates:
            print("[AUDIO] El micrófono no está disponible.")
            return None

        frecuencia = self.input_sample_rate or self.sample_rate
        canales = self.input_channels or self.channels
        frames_por_bloque = max(1, int(frecuencia * bloque_ms / 1000))
        bloques_silencio = max(
            1,
            int(silencio_final * frecuencia / frames_por_bloque)
        )
        bloques_espera = max(
            1,
            int(espera_maxima * frecuencia / frames_por_bloque)
        )
        bloques_maximos = max(
            bloques_espera + 1,
            int(duracion_maxima * frecuencia / frames_por_bloque)
        )

        try:
            depuracion.depurar(
                "[DEBUG AUDIO] abriendo InputStream "
                f"device={self.input_device} samplerate={frecuencia} "
                f"channels={canales} blocksize={frames_por_bloque}"
            )
            with sd.InputStream(
                device=self.input_device,
                channels=canales,
                dtype="float32",
                samplerate=frecuencia,
                blocksize=frames_por_bloque
            ) as stream:
                depuracion.depurar("[DEBUG AUDIO] InputStream abierto")
                # El micrófono USB necesita estabilizarse, pero no debemos
                # consumir el inicio de la frase del usuario.
                bloques_arranque = max(1, int(0.2 * frecuencia / frames_por_bloque))
                for _ in range(bloques_arranque):
                    depuracion.depurar("[DEBUG AUDIO] antes de esperar audio arranque")
                    stream.read(frames_por_bloque)
                    depuracion.depurar("[DEBUG AUDIO] después de recibir audio arranque")

                calibracion = []
                for _ in range(max(1, int(0.2 * frecuencia / frames_por_bloque))):
                    depuracion.depurar("[DEBUG AUDIO] antes de esperar audio calibración")
                    bloque, _ = stream.read(frames_por_bloque)
                    depuracion.depurar("[DEBUG AUDIO] después de recibir audio calibración")
                    calibracion.append(np.asarray(bloque, dtype=np.float32))

                ruido = np.concatenate(calibracion, axis=0)
                ruido = ruido.mean(axis=1)
                nivel_ruido = self._calcular_nivel_audio(ruido)
                nivel_usado, voz_en_calibracion = self._ruido_para_umbral(nivel_ruido)
                umbral = self._calcular_umbral_ruido(nivel_usado)
                depuracion.depurar(
                    f"[AUDIO] Calibración: ruido={nivel_ruido:.4f}; "
                    f"umbral={umbral:.4f}"
                    + (" (voz durante la calibración: se conserva)" if voz_en_calibracion else "")
                )

                bloques_audio = []
                pre_buffer = deque(
                    maxlen=max(2, int(0.24 / (bloque_ms / 1000)))
                )
                voz_detectada = False
                if voz_en_calibracion:
                    # Una respuesta rápida ("sí") empezó durante la
                    # calibración: ese audio es el inicio de la frase.
                    voz_detectada = True
                    bloques_audio.extend(
                        np.asarray(bloque, dtype=np.float32).mean(axis=1)
                        for bloque in calibracion
                    )
                silencio_consecutivo = 0
                voz_consecutiva = 0
                bloques_voz_inicio = self._bloques_minimos_inicio_voz(bloque_ms)

                for numero_bloque in range(bloques_maximos):
                    depuracion.depurar(
                        f"[DEBUG AUDIO] antes de esperar audio bloque={numero_bloque}"
                    )
                    bloque, _ = stream.read(frames_por_bloque)
                    depuracion.depurar(
                        f"[DEBUG AUDIO] después de recibir audio bloque={numero_bloque}"
                    )
                    cancelar = getattr(self, "cancelar", None)
                    if cancelar is not None and cancelar.is_set():
                        depuracion.depurar("[DEBUG AUDIO] escucha cancelada")
                        return None
                    bloque = np.asarray(bloque, dtype=np.float32)
                    bloque = bloque.mean(axis=1)
                    nivel = self._calcular_nivel_audio(bloque)

                    if not voz_detectada:
                        pre_buffer.append(bloque)
                        if nivel >= umbral:
                            voz_consecutiva += 1
                            if voz_consecutiva >= bloques_voz_inicio:
                                voz_detectada = True
                                bloques_audio.extend(pre_buffer)
                        else:
                            voz_consecutiva = 0
                        if not voz_detectada and numero_bloque >= bloques_espera:
                            depuracion.depurar(
                                "[AUDIO] No se detectó voz dentro del tiempo "
                                f"de espera (umbral={umbral:.4f})."
                            )
                            depuracion.depurar("[DEBUG AUDIO] finalizando captura sin voz")
                            return None
                        continue

                    bloques_audio.append(bloque)
                    if nivel < umbral:
                        silencio_consecutivo += 1
                    else:
                        silencio_consecutivo = 0

                    if silencio_consecutivo >= bloques_silencio:
                        break

                if not bloques_audio:
                    depuracion.depurar("[DEBUG AUDIO] captura finalizada sin bloques de audio")
                    return None

                audio = np.concatenate(bloques_audio)
                audio = audio - np.mean(audio)
                audio = np.clip(audio, -1.0, 1.0)
                audio = np.where(
                    audio < 0,
                    audio * 32768.0,
                    audio * 32767.0
                ).astype(np.int16)

                if frecuencia != self.sample_rate:
                    cantidad = int(round(len(audio) * self.sample_rate / frecuencia))
                    posiciones = np.linspace(0, len(audio) - 1, cantidad)
                    audio = np.interp(
                        posiciones,
                        np.arange(len(audio)),
                        audio
                    ).astype(np.int16)

                duracion_real = len(audio) / self.sample_rate
                print(
                    f"[AUDIO] Voz capturada: {duracion_real:.1f}s; "
                    f"umbral={umbral:.4f}"
                )
                depuracion.depurar("[DEBUG AUDIO] captura finalizada con voz")
                return np.asarray(audio, dtype=np.int16).tobytes()

        except Exception as exc:
            print(f"[AUDIO] Falló la grabación por actividad de voz: {exc}")
            depuracion.depurar(f"[DEBUG AUDIO] excepción en grabación: {type(exc).__name__}: {exc}")
            return None