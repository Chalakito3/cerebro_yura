# Rendimiento, temperatura y memoria de la Raspberry Pi 5 — 08/10/2026

Complementa el Informe N.º 002. Datos tomados en la Raspberry Pi 5 de Yura (Model B Rev 1.0, procesador Cortex-A76 de 4 núcleos a 2,4 GHz como máximo, 8 GB de RAM) durante la comparación de Whisper tiny con Vosk del 08/10/2026 (`entrenar_whisper_tiny.py`), la carga más pesada que ha tenido el equipo, y en reposo después de terminar.

## 1. Mediciones

| Momento | Temp. | Freno por calor | Frecuencia | Ventilador | Uso del procesador | Memoria en uso |
|---|---|---|---|---|---|---|
| Entrenamiento, 18:42 | 82,3 °C | activo | — | máximo | 292 % de 400 % (3 de 4 núcleos) | 3,7 de 7,9 GB (Whisper: 2,3 GB) |
| Entrenamiento, 19:00 | 81,8 °C | — | — | máximo | alto | — |
| Entrenamiento, 19:05 | 79,6 °C | no activo | 2,4 GHz | 7.158 RPM (nivel 4 de 4) | alto | — |
| Caja abierta, 19:08 | 81,2 °C | no activo | 2,4 GHz | 7.122 RPM | alto | — |
| Reposo, después | 47 °C | no activo | 1,7 GHz (ahorro) | detenido | 7-10 % | 1,7 de 7,9 GB |

- La Raspberry Pi 5 baja su velocidad a partir de unos 80 °C. El registro `throttled=0xe0008` a las 18:42 indica freno por temperatura activo en ese momento; en reposo queda `0xe0000`, que solo recuerda que hubo freno desde el último encendido.
- Alimentación: 5,15 V en reposo, sin avisos de bajo voltaje en esta sesión. (En los primeros días hubo bajo voltaje con otra fuente; ver Informe N.º 002, sección 1.)

## 2. Duración de la comparación

| Paso | Inicio | Duración aprox. |
|---|---|---|
| 1. Vosk con su proceso | 17:17 | 8 min |
| 2. Whisper tiny tal cual | 17:25 | 26 min |
| 3. Whisper tiny + el mismo proceso que Vosk | 17:51 | 42 min |
| 4. Reentrenar Whisper tiny (968 audios, 4 épocas) | 18:33 | 27 min |
| 5. Medir el reentrenado | 19:00 | 15 min |
| Total | | ≈ 2 h |

Whisper tiny tardó 1,2-1,3 s por audio en la Pi; Vosk, 0,49 s. El paso 6 previsto se omitió por tiempo.

## 3. Qué limita la velocidad

- **El procesador**, no la memoria. Durante el entrenamiento quedaban 4,2 GB libres; dar más memoria a Whisper (por ejemplo, 6 GB) no lo acelera, porque su trabajo son cálculos y los 4 núcleos ya iban casi al máximo. La RAM de la Pi 5 viene soldada y no se puede ampliar; este equipo ya tiene 8 GB.
- **La temperatura.** Por encima de 80 °C la Pi se frena sola. Enfriarla por debajo de ese límite evita el freno, pero no la hace más rápida que 2,4 GHz: a 40 °C rinde igual que a 70 °C. Con el ventilador al máximo y la caja abierta siguió cerca de 80 °C durante el entrenamiento.

Estimación (no medida) de lo que se ganaría en una carga como esta:

| Cambio | Ganancia aprox. | Observación |
|---|---|---|
| Mantenerla bajo 80 °C (más ventilación) | ~15 % | evita el freno |
| Subir la frecuencia a ~2,8 GHz | ~15-20 % | requiere buena refrigeración; puede volver inestable el sistema |
| Más memoria | 0 % | la memoria no era el límite |
| Una computadora con GPU (como la anterior, GTX 1650) | 10 veces o más | otro equipo |

## 4. Uso normal en clase

En el uso normal Yura no se acerca a estos límites: Vosk responde en 0,49 s y la decisión con el diccionario en 0,005 s (Informe N.º 002, sección 6). El calor y la velocidad solo importan en entrenamientos largos como este, que se hacen de vez en cuando.

**Recomendaciones:** para entrenamientos largos, dejar espacio libre alrededor del ventilador o agregar ventilación externa, y no tapar la caja. Usar la fuente oficial de 27 W (5 V, 5 A) para evitar bajo voltaje. No hace falta subir la frecuencia para el uso en clase.

**Límites:** las temperaturas se tomaron en momentos sueltos, no como registro continuo; las ganancias de la sección 3 son estimaciones. No se probó subir la frecuencia.
