---
name: yura-raspberry
description: Usar cuando se trabaja con el proyecto Yura (el robot educativo de quechua) directamente en una Raspberry Pi 5, o cuando el usuario pide instalar, migrar, diagnosticar o ajustar Yura para esa Raspberry Pi. Da por sentado el hardware (Pi 5, 8GB, Raspberry Pi OS) y los puntos ya revisados de compatibilidad, para no tener que re-investigarlos cada vez.
---

# Yura en Raspberry Pi 5

Este proyecto (`cerebro_yura`) se desarrolló originalmente en una compu de
escritorio (Ubuntu, GNOME, GPU NVIDIA) y se trasladó a una **Raspberry Pi 5
(8 GB RAM, Raspberry Pi OS de 64 bits)**. La guía completa de migración y la
lista de verificación están en `docs/RASPBERRY_PI5.md` —
leerla antes de instalar o diagnosticar algo por primera vez en esta máquina.

## Lo que ya se sabe de esta máquina (no hay que re-investigarlo)

- **No hay GPU NVIDIA ni CUDA.** El código ya detecta esto solo
  (`YURA_ASR=auto` en `main_robot.py`) y usa **Vosk** para reconocer voz en
  vivo, no Whisper. No forzar `YURA_ASR=whisper`: sin GPU es lento.
- **Vosk le gana a Whisper tiny en la Pi** (90 % vs 52 %, 0,6 s vs 3,6 s con
  la voz real de la docente): no cambiar a Whisper. Para que aprenda:
  `basedatos/aprender_de_audios.py --vosk` y `basedatos/entrenar_ordenes.py`
  (ver docs/RASPBERRY_PI5.md). "apágate" no está en el vocabulario de Vosk; sus
  deformaciones se mapean en `pronunciaciones.afinar_vosk`.
- **La Pi 5 no tiene jack de audio 3.5mm.** El parlante tiene que estar
  conectado por USB real (tarjeta de sonido USB), HDMI o Bluetooth — nunca un
  cable de audio analógico a un jack que no existe en esta placa. Si el
  audio no sale, lo primero es confirmar cómo está conectado el parlante.
- **El escritorio es Wayfire/labwc (Wayland), no GNOME.** El autologin se
  configura con `raspi-config` (System Options → Boot / Auto Login →
  Desktop Autologin), no con GDM, aunque el servicio de systemd
  (`scripts/yura.service`) y el arranque automático funcionan igual.
- **El navegador de pantalla completa es Chromium** (el que viene instalado
  por defecto), vía `scripts/yura-open-browser.sh`, que ya elige automático
  entre `firefox`, `firefox-esr` o `chromium`/`chromium-browser` según lo que
  encuentre — no hace falta instalar Firefox a propósito.
- **`torch==2.14.0` y `vosk==0.3.45` sí tienen build ARM64 (aarch64)** para
  Python 3.11/3.12/3.13. La Pi real tiene **Debian 13 (trixie) con
  Python 3.13**. Ojo: torch de PyPI en ARM64 arrastra paquetes CUDA de
  NVIDIA (GB inútiles); instalar antes `torch==2.14.0 --index-url
  https://download.pytorch.org/whl/cpu`. El resto de `requirements.txt` es
  puro Python. La instalación es igual que en la guía
  (`docs/comandos_yura.txt`): venv + `pip install -r requirements.txt`.
- **El modelo de Vosk (`model/`, 58 MB) está versionado en git**, así que
  viene con el proyecto sin pasos extra.
- **`diccionario.db`, `basedatos/pronunciaciones/`,
  `basedatos/pronunciaciones_yura/` y `.env.local` NO están en git**
  (`.gitignore`): si algo de eso falta después de trasladar el proyecto, hay
  que copiarlo a mano desde la compu original, o reconstruir el diccionario
  con `python basedatos/crear_diccionario.py` desde la semilla versionada.
- **Entrenar la voz** (`basedatos/entrenar_voz_yura.py`, kNN-VC) y
  **aprender de audios** (`basedatos/aprender_de_audios.py`, Whisper) corren
  bien en CPU (ya están pensados para eso), pero más lento por palabra que en
  una compu de escritorio. Es normal, no es un error.

## Cómo diagnosticar problemas nuevos en esta máquina

1. Primero descartar si el problema es específico de la Pi (hardware/SO) o
   si ya existía en la compu original: revisar `git log` y
   `documentacion_pruebas/` por si ya se investigó algo parecido.
2. Para audio, usar `wpctl status`, `aplay -l`, `arecord -l` y `lsusb` como en
   la compu original (PipeWire/WirePlumber es igual en ambas).
3. Si algo de `requirements.txt` falla al instalar, primero sospechar de la
   arquitectura (aarch64) o de la versión de Python antes de asumir que el
   paquete no existe — casi todo lo usado en este proyecto sí tiene build
   ARM64, según lo verificado arriba.
4. Seguir usando `journalctl --user -u yura -f` y `YURA_DEBUG=1` igual que en
   la compu original (`docs/comandos_yura.txt`); nada de eso cambia
   por estar en una Pi.
