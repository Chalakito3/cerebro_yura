# Registro de cambios — Ciclo 1 (fases 3 a 5)

**Fecha:** 27/09/2026 · **Alcance:** solo el cerebro de Yura (la plataforma Laravel no está en esta computadora) · **Vocabulario quechua:** sin cambios (espera aprobación).

## Cambios realizados

| # | Problema | Cambio | Archivos | Pruebas | Estado |
|---|---|---|---|---|---|
| P3 | `/resultados`, `/api/resultados` y `/resultados.csv` visibles para toda la red WiFi | Desde la propia computadora se ven sin clave; desde otro equipo piden la contraseña `YURA_RESULTADOS_CLAVE` (HTTP Basic, comparación segura con `hmac`); sin contraseña configurada, responden 403 | `web/app.py`, `.env.example` | 4 nuevas + prueba en vivo: desde 192.168.40.194 → 403; pantalla `/` → 200 | 🟢 VERIFICADO |
| P2 | En modo silencio la voz del aula se enviaba a Google | En silencio solo se usa Whisper local (`escuchar_voz(solo_local=True)`) | `main_robot.py` | 3 nuevas | 🟢 VERIFICADO (con pruebas); ⚫ sin prueba con micrófono real |
| P7 | La clave de Groq se buscaba ejecutando bash/zsh con `shell=True` y leyendo `.bashrc`, `.profile` y `.zshrc` | Solo se lee del entorno o de `.env.local` | `main_robot.py` | Suite completa | 🟢 VERIFICADO |
| — | `.env.local` guardado desde Windows (con BOM) perdía la primera clave | Lectura con `utf-8-sig` | `main_robot.py` | 1 nueva | 🟢 VERIFICADO |
| P8 | 88 % del registro eran mensajes técnicos y guardaba lo que decían los niños | Nuevo `depuracion.py`: mensajes técnicos y lo dicho por estudiantes solo con `YURA_DEBUG=1`; sin él se anota solo la cantidad de palabras. También se silenció el registro de las peticiones `/api/status` (≈17.000 al día) | `depuracion.py` (nuevo), `main_robot.py`, `audio_manager.py`, `conversacion.py`, `traductor.py`, `juego.py`, `web/app.py` | 2 nuevas + en vivo: 19 líneas en el primer minuto (con arranque) y 0 peticiones de estado anotadas en 20 s | 🟢 VERIFICADO |
| P6 | Código sin uso | Quitados: `AudioManager.grabar`, `_es_jack_directo`, `_es_entrada_logitech`, `_fuente_predeterminada_es_logitech`, la carga de Vosk (`_cargar_modelo_vosk`, `import vosk`) y el enlace a `style-draft.css` con el tema `?theme=soft` | `audio_manager.py`, `main_robot.py`, `web/templates/index.html`, `requirements.txt` | Búsqueda de referencias antes de quitar (0 usos) + suite completa + pantalla verificada | 🟢 VERIFICADO |
| P12 | Librerías sin versión fija | Versiones exactas de las que funcionan hoy (comprobado con `pip install --dry-run`: nada que cambiar) | `requirements.txt` | Suite completa | 🟢 VERIFICADO |
| — | Notas de uso | Cómo ver resultados desde otro equipo y cómo diagnosticar con `YURA_DEBUG=1` | `comandospara ejecutaryura.txt` | — | 🟢 |

**Pruebas automáticas:** 99 → **109**, todas pasan.

## No se hizo en este ciclo (y por qué)

| # | Tarea | Motivo | Estado |
|---|---|---|---|
| P1 | Corregir vocabulario | Espera aprobación palabra por palabra | ⚫ BLOQUEADO |
| P4, P11 | Juego y tarjetas desde el diccionario | Enseñarían las ~70 palabras aún incorrectas; se hará después de P1 | ⚫ BLOQUEADO |
| P5 | Conexión con la plataforma | La plataforma no está en esta computadora | ⚫ BLOQUEADO |
| P9 | Pantalla de 7" | Falta saber la pantalla real | ⚫ BLOQUEADO |
| P10 | Latencia con micrófono real | Requiere una persona hablando | 🟡 PENDIENTE |
| — | Borrar `model/` (58 MB), `entrada.txt`, `style-draft.css` y los respaldos del diccionario | Sin uso, pero pueden servir (Vosk para detectar "despierta" sin internet) | [PENDIENTE DE VALIDACIÓN] |
| P14 | Guardar en Git | El usuario pidió no usar Git por ahora | ⚫ BLOQUEADO |

## Riesgos nuevos o que siguen

- La contraseña de resultados viaja **sin cifrar** por la red WiFi (HTTP, no HTTPS). Es aceptable dentro del aula, no en una red pública. MEDIO.
- Sin Git, **no hay historial ni respaldo** de todo el trabajo. ALTO.
- La privacidad fuera del modo silencio (voz enviada a Google, Groq y Microsoft) sigue sin aviso ni consentimiento documentado. CRÍTICO.

**Estado: PROYECTO NO VERIFICADO — EXISTEN PENDIENTES.**
