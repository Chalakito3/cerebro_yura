# Registro de cambios — Yura aprende de los audios de la docente

**Fecha:** 27/09/2026 · **Pruebas automáticas:** 164 → **174**, todas pasan.

## Qué se hizo

| Cambio | Archivos | Prueba |
|---|---|---|
| Yura vuelve a escuchar las 100 grabaciones de la docente en 3 situaciones (menú, juego, sin pistas) y guarda cómo escribe el reconocedor cada palabra bien dicha (tabla `pronunciaciones_aprendidas`) | `basedatos/aprender_de_audios.py`, `pronunciaciones.py` | 1 prueba + ejecución real (evidencia `evidencias/13_aprendizaje_audios.txt`) |
| Las consultas encuentran la palabra aunque el reconocedor la escriba distinto ("qumir", "kumir", "omer" → Q'umir) | `traductor.py` (`_buscar_quechua_aproximado`) | 2 pruebas |
| Filtro de seguridad: no se usan para calificar transcripciones muy cortas ("oh"), la palabra vulgar *ullu* (Laime 2007), otra palabra del diccionario, ni frases que no se parecen ("adios", "thank you") | `pronunciaciones.py` (`variante_segura`) | 6 pruebas |
| El evaluador distingue *chay* de *kay* y acepta "puyu" por *phuyu* (antes "ph"+"u" se volvía "w") | `texto.py` | 1 prueba + las existentes |

## Resultado (sobre los 100 audios de la docente)

| Situación | Antes | Después |
|---|---|---|
| Menú / consultas | 56 % | 85 % |
| Juego | 77 % | 92 % |
| Sin pistas | 49 % | 80 % |

**Límite:** la medición usa los mismos audios de los que Yura aprendió (la voz de la docente). Con otras voces, por ejemplo niños, la mejora será menor. Falta medirla con voces reales.
