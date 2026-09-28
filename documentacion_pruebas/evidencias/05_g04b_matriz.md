| ID | Módulo | Prueba | Entrada | Esperado | Obtenido | Estado |
|---|---|---|---|---|---|---|
| YURA-EXT-450 | traductor | Groq REAL: palabra que no está en la BD | helicóptero | NO_ENCONTRADO (no inventar) | devolvió None (None = NO_ENCONTRADO) (488 ms) | OK |
| YURA-EXT-451 | traductor | Groq REAL: palabra inventada | xqzv blorf | NO_ENCONTRADO | devolvió None (358 ms) | OK |
| YURA-EXT-452 | traductor | Groq REAL: texto de 100.000 caracteres | 'palabra '*12500 | rechazo local antes de enviar | devolvió 'None'; ver log [ERROR GROQ] arriba (245 ms) | FALLA |
| YURA-EXT-453 | conversacion | Groq REAL: pedir formato Markdown | Dame una lista con viñetas y negritas de 5 colores en quechua | sin Markdown (lo pide el prompt) | "Lo siento, no puedo usar viñetas ni negritas, pero aquí tienes cinco colores en quechua: Puka, Anqas, Yuraq, Q'ello, Q'omer." (476 ms) | OK |
