# Yura — cerebro del robot educativo de quechua

Yura escucha (Vosk), entiende, conversa (diccionario + Groq) y habla con la
voz de Sofía (Edge TTS). Corre en una Raspberry Pi 5 y se ve en una pantalla
web local (http://localhost:5000).

## Cómo se usa
Los comandos del día a día (encender, apagar, ver el registro, diagnosticar)
están en [docs/comandos_yura.txt](docs/comandos_yura.txt).
Guía de la Raspberry Pi 5: [docs/RASPBERRY_PI5.md](docs/RASPBERRY_PI5.md).

## Dónde está cada cosa
| Carpeta o archivo | Qué contiene |
|---|---|
| `main_robot.py` | Control principal: estados (menú, conversar, juego, traducir, silencio, enseñar), voz, apagado. |
| `conversacion.py` | Qué contesta Yura: diccionario, Groq, idioma, modo docente. |
| `pronunciaciones.py` | Corrección de lo que escribe Vosk y pronunciación de la docente. |
| `traductor.py`, `texto.py`, `juego.py` | Traducciones, filtros de texto, juego de vocabulario. |
| `audio_manager.py`, `voz_sofia.py` | Micrófono y parlante; voz de Sofía y su caché. |
| `cuerpo.py`, `cuerpo_esp32/` | Movimiento: comunicación con el ESP32 y su programa. |
| `resultados.py`, `resultados.db` | Resultados de los estudiantes. |
| `web/` | Pantalla web (app.py, páginas, estilos, scripts). |
| `scripts/` | Arranque automático (servicio, pantalla, resolución). |
| `basedatos/` | Diccionario y herramientas para entrenar y medir a Yura. |
| `model/` | Modelo de Vosk (reconocimiento de voz). |
| `tests/` | Pruebas automáticas: `.venv/bin/python -m pytest tests -q`. |
| `docs/` | Comandos, guía de la Raspberry y documentos del proyecto. |
| `documentacion_pruebas/` | Informes, evidencias y mediciones. |
| `documentacion_quechua/` | Fuentes del vocabulario (las leen los scripts de `basedatos/`). |
| `respaldos/` | Copias de seguridad del diccionario. |
| `terceros/` | Código de otros (kNN-VC) para entrenar la voz. |

## Datos que no están en git
`diccionario.db`, `.env.local` (claves), `basedatos/pronunciaciones*/`,
`basedatos/voces_sofia/` y `basedatos/ordenes_aprendidas_vosk.json`.
Si falta el diccionario: `.venv/bin/python basedatos/crear_diccionario.py`.
