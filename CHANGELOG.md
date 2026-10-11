# Historial de versiones

Yura usa versiones `MAYOR.MENOR.PARCHE` (versionado semántico):

- **PARCHE** (0.3.**1**): corrige fallas sin cambiar lo que Yura hace.
- **MENOR** (0.**4**.0): agrega funciones o cambia el comportamiento.
- **MAYOR** (**1**.0.0): primera versión validada en clase con estudiantes; después, cambios que obligan a reinstalar o rehacer datos.

La versión actual está en el archivo `VERSION`, se muestra al arrancar y en `/api/status`. Cada versión publicada lleva una etiqueta de git (`v0.3.0`). El programa del ESP32 tiene su propia numeración (`YURA_CUERPO v6`).

## [0.3.0] — 2026-10-11 — Raspberry Pi 5

Traslado de la computadora de escritorio (GPU NVIDIA) a la Raspberry Pi 5. Detalle en `documentacion_pruebas/avance_raspberry_2026-10-07.md` y `avance_2026-10-11.md`.

**Agregado**
- Reconocimiento con Vosk en la CPU (`YURA_ASR=auto`), con lo aprendido de los audios de la docente (88 % de sus palabras).
- Voz de Sofía sin internet: frases guardadas para todo lo que Yura dice.
- Entrenamiento de órdenes con la voz de quien usa a Yura (`entrenar_ordenes.py`).
- Afinado de la pronunciación de Sofía hacia la docente (`afinar_pronunciacion.py`); modo `--solo-no-entendidas --priorizar-entender`: la voz de Sofía pasó de 86 % a 91 % de palabras entendidas.
- Escucha entrenada con la voz de Sofía (`aprender_voz_sofia_vosk.py`): las 328 palabras del diccionario, sin aprender castellano común.
- Cuerpo con ESP32 (programa v6): movimiento por voz, límite de 3 s, freno ante obstáculos y `SENSORES:OFF/ON` para pruebas.
- Pedido de hablar en español aunque Vosk deforme la frase («conversa en español»).
- Control de traducciones: si Groq enseña una palabra quechua que no está en el diccionario («fútbol se dice pukllay bola»), esa oración se cambia por «Esa palabra todavía no está en mi diccionario».
- Arranque automático en la Pi (labwc), resolución 1080p en televisores 4K.
- Versión del producto (`VERSION`, este historial, `/api/status`).

**Cambiado**
- Silencio para dar por terminada la frase: 1,0 s → 0,7 s (`YURA_SILENCIO_FINAL`).
- Yura no describe emociones ni gestos.
- Tatay, Mamay, Wawqiy y Ñañay se traducen sin «mi».
- Comandos y guía de la Pi movidos a `docs/`; `README.md` con el mapa del proyecto.

**Corregido**
- Yura muda: la ruta con espacio final rompía `edge-tts` y el servicio.
- Kiosco que no abría si ya había un Chromium abierto.
- La palabra en negrita («**Allqu jatun**») se borraba junto con los gestos.

## [0.2.0] — 2026-09-28 — Auditoría, voz y modo docente

Commits `ec5efaa` y `e23cdf2`. Detalle en `documentacion_pruebas/informe_001_2026-09-27.md`.

- Correcciones de la auditoría, modo docente con grabación de pronunciaciones, aprendizaje de los audios de la docente, voz boliviana, colores de la unidad educativa.

## [0.1.0] — 2026-09-26 — Primera versión

Commit `aac001b`. Cerebro inicial: menú, conversación, juego, traductor y pantalla web.
