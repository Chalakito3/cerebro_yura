# Registro de cambios — Ciclo 3 (reconocimiento de voz y voz de Yura)

**Fecha:** 27/09/2026 · **Pruebas automáticas:** 137 → **151**, todas pasan.

## Medición (evidencias en `evidencias/11_voz/`)

96 audios: 24 frases típicas (órdenes, preguntas y palabras quechuas) dichas con 4 voces distintas a la de Yura (2 bolivianas, 1 peruana, 1 ecuatoriana). Limitación: son voces sintéticas de adultos, no niños reales.

| Motor | Frases entendidas | Tiempo por frase |
|---|---|---|
| Whisper base local (el respaldo anterior) | 67/96 = 70 % | 0,26 s |
| Groq Whisper large-v3-turbo (internet) | 72/96 = 75 % | 3,75 s |
| Whisper small local | 74/96 = 77 % | 0,89 s |
| Gemini (el principal anterior) | ❌ no respondió: agotó la espera de 12 s | 12,2 s |
| **Whisper small + pistas + evaluador (código real de Yura)** | **90/96 = 94 %** | **0,85 s** |

Los errores estaban en palabras quechuas sueltas escritas con letras del castellano ("Base" por *wasi*, "Algo" por *allqu*, "Jaco" por *yaku*, "Cuyju" por *q'illu*).

## Cambios

| Cambio | Archivos | Prueba |
|---|---|---|
| Whisper **small** como reconocedor (antes base) | `main_robot.py` | Medición + arranque real (6 s, 2,2 de 4 GB de video) |
| **Pistas de vocabulario** al reconocedor: en el juego, la respuesta mezclada con las otras palabras de la partida y 3 más; en la práctica, la palabra a repetir y 5 más; en el resto, 14 palabras frecuentes | `texto.py` (`instruccion_reconocedor`), `juego.py`, `conversacion.py` (`pistas_practica`), `main_robot.py` | 3 pruebas automáticas |
| **Evaluador** que entiende cómo escribe el reconocedor: b/v = w, g = k, j = y, "ll" como l o y. Sigue rechazando palabras distintas (*wawa*/Tawa, *yana*/Llama) y todas las palabras del diccionario se aceptan a sí mismas | `texto.py` | 8 pruebas + verificación con las 187 palabras |
| **Gemini desactivado por defecto** (no respondía, 20 usos diarios, envía la voz de los niños a Google). Si se activa (`YURA_GEMINI_ENABLED=1`): espera máxima 6 s y pausa de 10 min tras un fallo | `gemini_transcriber.py`, `.env.example` | 2 pruebas |
| **Voz boliviana Sofía** (`es-BO-SofiaNeural`), elegida por el equipo tras escuchar 3 muestras; configurable con `YURA_VOZ` | `main_robot.py`, `.env.example` | 1 prueba + saludo real sin errores |

## Efecto en privacidad

Con Gemini desactivado, **la voz de los estudiantes ya no sale de la computadora** en ningún modo: se transcribe con Whisper local. Siguen yendo a internet el **texto** de la conversación libre (Groq) y el texto que Yura dice (voz de Microsoft Edge).

## Pendiente

- Medir con **voces reales de niños** (las pruebas usan voces sintéticas de adultos). 🟡
- Se puede seguir mejorando *Allqu*, *Q'illu* y *Wasi*, que fallan a veces aun con pistas. 🟡
