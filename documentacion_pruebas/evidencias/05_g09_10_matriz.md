| ID | Módulo | Prueba | Entrada | Esperado | Obtenido | Estado |
|---|---|---|---|---|---|---|
| YURA-EXT-901 | claves | cargar_archivo_claves | 'YT_BOM' | 'valor_bom' | None (quedó guardada como '\ufeffYT_BOM') (0 ms) | FALLA |
| YURA-EXT-902 | claves | cargar_archivo_claves | 'YT_SIN_IGUAL' | None | None (0 ms) | OK |
| YURA-EXT-903 | claves | cargar_archivo_claves | 'YT_DOBLES' | 'con comillas' | 'con comillas' (0 ms) | OK |
| YURA-EXT-904 | claves | cargar_archivo_claves | 'YT_SIMPLES' | 'simples' | 'simples' (0 ms) | OK |
| YURA-EXT-905 | claves | cargar_archivo_claves | 'YT_MIXTAS' | None | 'abre doble cierra simple' (comillas desbalanceadas) (0 ms) | OBSERVACION |
| YURA-EXT-906 | claves | cargar_archivo_claves | 'YT_ESPACIOS' | 'con espacios' | 'con espacios' (0 ms) | OK |
| YURA-EXT-907 | claves | cargar_archivo_claves | 'YT_EXPORT' | 'exportada' | 'exportada' (0 ms) | OK |
| YURA-EXT-908 | claves | cargar_archivo_claves | 'YT_EXPORT2' | 'doble espacio' | 'doble espacio' (0 ms) | OK |
| YURA-EXT-909 | claves | cargar_archivo_claves | 'YT_COMENTARIO' | 'valor' | 'valor # comentario en línea' (0 ms) | OBSERVACION |
| YURA-EXT-910 | claves | cargar_archivo_claves | 'YT_VACIA' | None | None (0 ms) | OK |
| YURA-EXT-911 | claves | cargar_archivo_claves | 'YT_IGUAL' | 'a=b=c' | 'a=b=c' (0 ms) | OK |
| YURA-EXT-912 | claves | cargar_archivo_claves | 'YT_DUP' | 'segunda' | 'primera' (convención dotenv: gana la última) (0 ms) | OBSERVACION |
| YURA-EXT-913 | claves | cargar_archivo_claves | 'YT_CRLF' | 'windows' | 'windows' (0 ms) | OK |
| YURA-EXT-914 | claves | cargar_archivo_claves | 'YT_SOLO_COMILLAS' | None | None (0 ms) | OK |
| YURA-EXT-915 | claves | cargar_archivo_claves | 'yt minus' | None | 'con espacio en la clave' (0 ms) | OBSERVACION |
| YURA-EXT-916 | claves | cargar_archivo_claves | 'YT_COMENTADA' | None | None (0 ms) | OK |
| YURA-EXT-930 | claves | cargar_archivo_claves con .env.local sin permisos | chmod 000 | aviso sin excepción | sin excepción (ver [ALERTA CLAVES] en log) (0 ms) | OK |
| YURA-EXT-931 | claves | '.env.local' es una carpeta | directorio | ignorar sin excepción | sin excepción (0 ms) | OK |
| YURA-EXT-932 | claves | '.env.local' binario | bytes 0-255 | sin excepción | sin excepción (0 ms) | OK |
| YURA-EXT-950 | main_robot | _set_web_status/get_web_status desde 16 hilos | 8 escritores x5000 + 8 lectores x5000 | sin errores, content y translation siempre del mismo evento | errores=0 incoherentes=0 tiempo=0.25s (0 ms) | OK |
| YURA-EXT-951 | conversacion | Conexión SQLite de conversacion usada desde otro hilo | procesar_entrada('quiero practicar') en hilo 2 | funciona o error controlado | ProgrammingError: SQLite objects created in a thread can only be used in that same thread. The object was created in thread id 129989975695488 and this is thread id 129985541027520. (0 ms) | FALLA |
| YURA-EXT-952 | traductor | db_conn compartida (check_same_thread=False) por 8 hilos | 8 x 200 búsquedas | sin errores | errores=6 ["IndexError('tuple index out of range')", "IndexError('tuple index out of range')"] (0 ms) | FALLA |
| YURA-EXT-953 | conversacion | Estado de práctica global (_sesion_educativa) compartido por módulo | otra parte del programa cancela la sesión | sesión por usuario/robot | tras cancelar, la respuesta correcta 'K'uchillu' ya no se evalúa: 'Soy Yura, un robot educativo que ayuda a practicar quechua. Puedo enseñarte voca' (1 ms) | OBSERVACION |
