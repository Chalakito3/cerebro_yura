**Correcciones del informe — primera etapa, 30/09/2026**

Enfoque: privacidad, validación HTTP, exportación y dependencia de reconocimiento.

- `/api/status` mantiene su disponibilidad pública, pero oculta participante, contenido, traducción y resultado a clientes remotos sin credenciales docentes válidas. Se conserva el acceso completo local y remoto autenticado. La comprobación de host local existente sigue vigente.
- Estado y rutas docentes envían `Cache-Control: no-store` para evitar almacenar respuestas sensibles en cachés.
- La exportación CSV antepone un apóstrofo a valores susceptibles de interpretarse como fórmulas, incluidos prefijos tras espacios. No modifica los valores almacenados en SQLite. La interpretación final sigue dependiendo del programa de hojas de cálculo.
- Las rutas de grabación y ajuste de voz rechazan JSON no compuesto por un objeto. Los identificadores no aceptan booleanos, fracciones ni valores no positivos; el texto de voz debe ser una cadena de hasta 80 caracteres. Se conserva el texto vacío para restablecer la voz.
- `requirements.txt` incluye `vosk==0.3.45`, versión ya instalada en el entorno auditado. `.env.example` documenta `YURA_ASR` y la necesidad del modelo local.

**Verificación:** 280 pruebas aprobadas, 1 omitida, 10,65 segundos. Se añadieron 45 casos parametrizados de regresión en `tests/test_correcciones_informe.py`. La suite se ejecutó en `/tmp/yura-correcciones-gh66moq8`, sin copiar claves y usando una copia consistente del diccionario. La omisión corresponde al respaldo histórico no copiado. Los escenarios válidos de voz y resultados existentes continúan pasando.

**Límites:** no se instaló nada ni se reinició el servicio. El proceso de Yura que ya estuviera ejecutándose cargará los cambios de código al reiniciarse. No se cambiaron bases de datos ni audios originales. No se modificó la evaluación lingüística, la selección ASR ni el despliegue HTTP. Continúan pendientes las demás observaciones del informe: validación independiente con docentes, arranque sin reconocedor, instalación limpia, respaldo/restauración integral, transporte cifrado remoto y mejoras de arquitectura. Esta etapa no demuestra que todo el informe esté resuelto.
