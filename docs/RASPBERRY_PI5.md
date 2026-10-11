# Migrar Yura a Raspberry Pi 5 (8 GB, Raspberry Pi OS)

Revisado el 2026-10-03 en la computadora de desarrollo (Ubuntu 24.04, x86_64).
Nadie probó esto todavía en una Raspberry Pi real: son los puntos verificados
por compatibilidad de paquetes y por las diferencias de hardware/SO conocidas.
Después de instalar, conviene repasar esta lista y tachar lo que ya funcionó.

## Resultado en la Pi real (2026-10-04)

Ya se instaló en la Raspberry Pi 5. Diferencias con lo previsto abajo:

- El sistema es **Raspberry Pi OS basado en Debian 13 (trixie)** con
  **Python 3.13**, no Bookworm/3.11. Todo funciona igual.
- El `.venv` copiado desde la otra compu **no sirve** (era Python 3.12 y x86).
  Se movió a `.venv_pc_x86_respaldo/` (se puede borrar) y se creó uno nuevo.
- **torch en ARM64 desde PyPI baja las librerías CUDA de NVIDIA** (triton,
  nvidia-*, varios GB inútiles en la Pi). Hay que instalar primero la
  versión solo CPU y después el resto:

  ```sh
  .venv/bin/pip install torch==2.14.0 --index-url https://download.pytorch.org/whl/cpu
  .venv/bin/pip install -r requirements.txt
  ```
- Faltaban `portaudio19-dev` y `espeak-ng`; ya instalados. `ffmpeg` ya trae
  `rubberband`.
- El autologin ya estaba activo (LightDM, sesión `rpd-labwc`), y labwc lee
  `~/.config/autostart` (vía `lxsession-xdg-autostart`), así que
  `yura.desktop` funciona sin cambios.
- Las 281 pruebas pasan y `web/app.py` arranca (Vosk, Groq y diccionario OK).
- Audio: tarjeta de sonido USB C-Media (0d8c:0012) con parlante y micrófono;
  Yura la elige sola. En el primer puerto USB daba error -71 (la Pi registró
  bajo voltaje); en otro puerto funcionó. Si vuelve a fallar, revisar fuente.

## Reconocimiento de voz en la Pi (Vosk) — medido el 2026-10-04

Con las 121 grabaciones reales de la docente:

| Motor | Entiende bien | Tiempo por audio |
|---|---|---|
| Vosk (con lo aprendido) | 89-90 % | 0,6 s |
| Whisper tiny | 52 % | 3,6 s |

Por eso en la Pi se usa Vosk (`YURA_ASR=auto` ya lo elige). Vosk no tiene en
su vocabulario "apágate" ni "Yura": las escribe como "gate", "para date",
"apaga te", "jura"... `pronunciaciones.afinar_vosk` las convierte en la orden.

Para que Vosk aprenda (detener antes a Yura: `systemctl --user stop yura`):

```sh
# Las palabras de la docente, escuchadas con Vosk (después de grabar nuevas):
.venv/bin/python basedatos/aprender_de_audios.py --vosk
# Las órdenes con la voz de quien usa a Yura (Yura pide decir cada una 3 veces):
.venv/bin/python basedatos/entrenar_ordenes.py
```

La pronunciación de Yura (voz de Sofía, necesita internet) se sigue afinando con
`nice -n 19 .venv/bin/python basedatos/afinar_pronunciacion.py --rondas 8 --procesos 2`
(119 palabras ≈ 67 min en la Pi). Parte de lo ya guardado y solo lo cambia si
queda ≥ 3 % más parecido a la docente; no toca lo fijado por la docente.

Lo aprendido de las órdenes queda en `basedatos/ordenes_aprendidas_vosk.json`
(no está en git). Solo se aprende lo que Vosk escribió igual al menos 2 veces.

## Cuerpo de Yura: pines del ESP32 (DevKit V1)

Cableado del equipo (07/10/2026), con los brazos ya movidos de D34/D35 (solo
entradas, no pueden mandar señal) a D15/D33.

- Programa del ESP32: `cuerpo_esp32/yura_cuerpo/yura_cuerpo.ino` (responde
  `YURA_CUERPO v5`); cargar con `sh cuerpo_esp32/cargar.sh` (arduino-cli en
  `~/.local/bin`, librería ESP32Servo).
- `cuerpo.py` busca el ESP32 por USB y le manda estados, gestos y movimientos;
  abre el puerto sin DTR/RTS (con ellos el CP2102 dejaba al ESP32 reiniciándose).
  Sin ESP32, Yura funciona igual; `YURA_CUERPO=0` en `.env.local` lo desactiva.
- Por voz: "avanza"/"camina hacia adelante", "retrocede", "gira a la
  izquierda/derecha", "para"/"detente". Máx. 3 s por movimiento; frena ante
  obstáculos a menos de 20 cm y si la Raspberry no manda nada en 5 s.

| Pieza | Pines |
|---|---|
| Ultrasónico adelante | Trig D23, Echo D22 |
| Ultrasónico izquierda | Trig D21, Echo D19 |
| Ultrasónico derecha | Trig D18, Echo D5 |
| Ultrasónico atrás | Trig D4, Echo D2 |
| L298N | ENA D13, IN1 D12, IN2 D14, IN3 D27, IN4 D26, ENB D25 |
| Servo brazo izquierdo | D15 |
| Servo brazo derecho | D33 |
| Servo cuello | D32 |

- Echo de los HC-SR04 da 5 V: divisor 1k/2k antes del ESP32.
- No usar D16 ni D17: en esta placa cuelgan el ESP32.
- D12 (IN1) se lee al arrancar: si el ESP32 no arranca con todo conectado,
  pasar IN1 a otro pin.
- Si una rueda gira al revés, intercambiar los 2 cables de ese motor en el L298N.

## 1. Lo más importante: el audio de salida

**La Raspberry Pi 5 no tiene jack de audio de 3.5mm** (a diferencia de la Pi 3/4).
El parlante actual de Yura se conecta con un cable de audio analógico a esa
salida (el cable USB del parlante es solo para alimentación, no lleva sonido).
Eso **no va a tener dónde conectarse** en la Pi 5.

Opciones, de más a menos recomendada:
- Un parlante o adaptador de audio **USB** (que se vea como tarjeta de sonido
  USB real, no solo alimentación).
- Salida de audio por **HDMI** (si la pantalla/TV tiene parlantes).
- Un parlante **Bluetooth** (la Pi 5 tiene Bluetooth integrado).

Sin resolver esto antes, Yura no va a tener por dónde hablar.

El micrófono USB actual sí debería funcionar igual (es un dispositivo de
entrada USB real, no depende del jack que falta).

## 2. Sistema operativo y escritorio

- Usar **Raspberry Pi OS de 64 bits** (Bookworm o más nuevo), no la versión de
  32 bits: paquetes como `torch` no tienen build de 32 bits para ARM.
- Raspberry Pi OS Bookworm trae **Wayfire/labwc** (Wayland) como escritorio
  por defecto, no GNOME. El arranque automático por `systemd --user` y el
  audio por PipeWire/WirePlumber deberían funcionar igual (no dependen del
  escritorio), pero:
  - El inicio de sesión automático se configura con
    `sudo raspi-config` → *System Options* → *Boot / Auto Login* →
    *Desktop Autologin*, no con GDM (el comentario en `scripts/yura.service`
    menciona GDM porque esta compu usa GNOME; en la Pi es otro mecanismo,
    pero el resultado — iniciar sesión sola — es el mismo).
  - `scripts/yura.desktop` usa claves `X-GNOME-Autostart-*`; es el estándar
    XDG y debería respetarlo igual el autoarranque de Raspberry Pi OS, pero
    conviene confirmarlo después de instalar.

## 3. Navegador para la pantalla completa

Raspberry Pi OS trae **Chromium** por defecto, no Firefox (y si se instala
Firefox vía `apt`, el paquete se llama `firefox-esr`, con el binario
`firefox-esr`, no `firefox`).

Ya ajusté `scripts/yura-open-browser.sh` para que use, en este orden, el
primero que encuentre: `firefox`, `firefox-esr`, `chromium-browser`,
`chromium`. No hace falta instalar Firefox a propósito: Chromium (el que ya
viene instalado) funciona tal cual.

## 4. Paquetes del sistema (equivalente al apt install de la compu actual)

```sh
sudo apt update
sudo apt install -y python3-venv python3-dev build-essential \
    portaudio19-dev espeak-ng ffmpeg git
```

Después de instalar, confirmar que `ffmpeg` tiene el filtro `rubberband`
(lo usa `basedatos/entrenar_voz_yura.py` para una de las dos técnicas de voz):

```sh
ffmpeg -filters | grep rubberband
```

Si no aparece nada, instalar `librubberband2` aparte
(`sudo apt install librubberband2`) y volver a revisar.

## 5. Python y dependencias (`requirements.txt`)

Raspberry Pi OS Bookworm trae **Python 3.11** (la compu actual usa 3.12; el
proyecto no usa nada específico de 3.12, así que no debería haber problema).

Ya confirmé contra PyPI que las versiones fijadas en `requirements.txt`
tienen build para Linux ARM64 (aarch64) en Python 3.11 y 3.12:

- `torch==2.14.0` → sí (`manylinux_2_28_aarch64`)
- `vosk==0.3.45` → sí (`manylinux2014_aarch64`, además del modelo en `model/`
  que ya está versionado en git — no hay que descargarlo aparte)
- El resto (`flask`, `groq`, `openai-whisper`, `sounddevice`, `numpy`,
  `google-genai`, `edge-tts`, `pytest`) son paquetes puro-Python o con build
  universal; no deberían dar problema.

Instalación (igual que en la compu actual):

```sh
cd "ruta/al/proyecto/cerebro_yura"
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## 6. Rendimiento esperado

- **Conversación en vivo (Vosk)**: ya está pensado para esto. El código elige
  Vosk automáticamente cuando no hay GPU NVIDIA (`YURA_ASR=auto`, el valor por
  defecto), que es exactamente el caso de la Pi 5. No hace falta cambiar nada.
- **Whisper** (reconocimiento más preciso pero pesado) no se debe forzar con
  `YURA_ASR=whisper` en la Pi: sin GPU va a ser lento. Dejarlo en `auto`.
- **Entrenar la voz de Yura** (`basedatos/entrenar_voz_yura.py`, usa kNN-VC
  con PyTorch) y **aprender de audios** (`basedatos/aprender_de_audios.py`,
  usa Whisper) corren sin GPU también en la compu actual, así que ya están
  pensados para CPU — pero en la Pi van a tardar más por palabra que en esta
  compu de escritorio. Como se corren de vez en cuando (no en tiempo real),
  no debería ser un problema, solo hay que tener paciencia la primera vez.

## 7. Qué transportar además del código

Estos archivos/carpetas **no están en git** (`.gitignore`) y hay que copiarlos
a mano si se quiere conservar lo aprendido hasta ahora:

- `diccionario.db` (o reconstruirlo desde la semilla:
  `.venv/bin/python basedatos/crear_diccionario.py`)
- `basedatos/pronunciaciones/` (grabaciones de la docente, modo docente)
- `basedatos/pronunciaciones_yura/` (voz de Yura ya entrenada)
- `basedatos/voces_sofia/` (caché de voz; se regenera solo, no es necesario)
- `.env.local` (las claves API — **no se suben a git a propósito**, copiar
  con cuidado y mantener `chmod 600`)

`model/` (el modelo de Vosk, 58 MB) **sí** está versionado en git, así que
viene solo con el proyecto.

## 8. Instalar el arranque automático

Una vez copiado el proyecto e instaladas las dependencias, el resto es igual
a como está documentado en `docs/comandos_yura.txt`:

```sh
sh scripts/instalar_arranque.sh
```

(después de configurar el autologin de escritorio con `raspi-config`, punto 2
de esta guía).

## Lista rápida de verificación

- [x] Raspberry Pi OS de 64 bits instalado
- [x] Parlante resuelto (tarjeta de sonido USB C-Media 0d8c:0012, salida + micrófono)
- [x] Micrófono detectado (entrada de la misma tarjeta C-Media)
- [x] Autologin de escritorio activado (`raspi-config`)
- [x] Paquetes del sistema instalados (sección 4)
- [x] `ffmpeg -filters | grep rubberband` muestra algo
- [x] `.venv` creado e instalado `requirements.txt` sin errores (torch CPU)
- [x] `diccionario.db`, `basedatos/pronunciaciones*/` y `.env.local` copiados
- [x] `sh scripts/instalar_arranque.sh` ejecutado
- [ ] Yura enciende sola al reiniciar y se escucha por el parlante elegido
