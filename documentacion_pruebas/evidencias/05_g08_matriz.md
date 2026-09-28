| ID | Módulo | Prueba | Entrada | Esperado | Obtenido | Estado |
|---|---|---|---|---|---|---|
| YURA-EXT-801 | audio | Ningún dispositivo | query_devices()=[] | input_device=None y grabar devuelve None | audio=None bloques=0 (0 ms) | OK |
| YURA-EXT-802 | audio | query_devices lanza excepción | OSError | sin excepción | audio=None (0 ms) | OK |
| YURA-EXT-803 | audio | Dispositivo que falla al abrir | check_input_settings lanza | None sin excepción | audio=None (0 ms) | OK |
| YURA-EXT-804 | audio | Silencio absoluto | ceros | None tras espera_maxima (10 s = 125 bloques) | audio=None bloques leídos=130 (5 ms) | OK |
| YURA-EXT-805 | audio | Ruido constante alto (0,3 medio) desde el inicio | uniforme ±0,6 | terminar como máximo en duracion_maxima (15 s) | devuelve 15.0 s de audio; bloques=191 (el ruido estable se calibra; umbral máx 0,104) (36 ms) | OBSERVACION |
| YURA-EXT-806 | audio | Ruido alto que empieza tras la calibración (TV/ventilador) | ceros y luego ±0,6 | terminar en duracion_maxima; no enviar 15 s de ruido al transcriptor | devuelve 14.8 s de audio; bloques=191 -> Gemini/Whisper reciben 15 s de ruido (24 ms) | OBSERVACION |
| YURA-EXT-807 | audio | Voz que empieza a los 9,6 s y dura mucho | silencio 120 bloques + voz continua | grabar hasta 15 s DESDE que empieza la voz | audio=5.2 s (duracion_maxima cuenta desde el inicio de la escucha, no desde la voz) (13 ms) | OBSERVACION |
| YURA-EXT-808 | audio | Clipping (amplitud 1,8 > 1,0) | onda cuadrada ±1,8 | int16 válido, sin overflow | 234240 muestras, max=32768 (27 ms) | OK |
| YURA-EXT-809 | audio | Bloques con NaN | NaN | None sin excepción | audio=None bloques=130 (5 ms) | OK |
| YURA-EXT-810 | audio | Parámetros extremos: bloque_ms=0 | bloque_ms=0 | error controlado | audio=None (112 ms) | OK |
| YURA-EXT-820 | audio | _calcular_umbral_ruido | 0 | valor en [0,006; 0,12] o error controlado | umbral=0.006 (0 ms) | OK |
| YURA-EXT-821 | audio | _calcular_umbral_ruido | -1 | valor en [0,006; 0,12] o error controlado | umbral=0.006 (0 ms) | OK |
| YURA-EXT-822 | audio | _calcular_umbral_ruido | nan | valor en [0,006; 0,12] o error controlado | umbral=0.006 (0 ms) | OK |
| YURA-EXT-823 | audio | _calcular_umbral_ruido | 1.0 | valor en [0,006; 0,12] o error controlado | umbral=0.10400000000000001 (0 ms) | OK |
| YURA-EXT-824 | audio | _calcular_umbral_ruido | inf | valor en [0,006; 0,12] o error controlado | umbral=0.10400000000000001 (0 ms) | OK |
| YURA-EXT-825 | audio | _calcular_umbral_ruido | None | valor en [0,006; 0,12] o error controlado | umbral=0.006 (0 ms) | OK |
| YURA-EXT-826 | audio | _calcular_umbral_ruido | 'abc' | valor en [0,006; 0,12] o error controlado | ValueError: could not convert string to float: 'abc' (solo recibe floats en el flujo real) (0 ms) | OBSERVACION |
| YURA-EXT-830 | audio | YURA_INPUT_DEVICE apunta a índice inexistente | 99 | usar otro dispositivo o avisar | input_device=0 (se ignora el índice y usa el disponible) (0 ms) | OK |
