| ID | Módulo | Prueba | Entrada | Esperado | Obtenido | Estado |
|---|---|---|---|---|---|---|
| YURA-EXT-601 | web | /api/status con robot None | GET | 200 BACKEND_NOT_STARTED | 200 BACKEND_NOT_STARTED (1 ms) | OK |
| YURA-EXT-602 | web | /api/status con get_web_status que lanza excepción | GET | JSON de error controlado (p. ej. 503) que app.js pueda mostrar | 500 content-type=text/html; charset=utf-8 cuerpo=b'<!doctype html>\n<html lang=en>\n<title>500 Internal Server Error</title>\n<h1>Inte' (1 ms) | FALLA |
| YURA-EXT-603 | web | /api/status con estado desconocido y web_status vacío | GET | 200 con valores por defecto | 200 {'activity': 'ACTIVIDAD DEL ROBOT', 'content': '', 'message': 'Yura está trabajando.', 'phase': 'ESPERANDO', 'result': None, 'robot': 'YURA', 'running': True, 'state': 'ESTADO_INVENTADO', 'translation': '', 'updated_at': '2026-09-27T04:23:20.527705+00:00'} (0 ms) | OK |
| YURA-EXT-604 | web | /api/status con robot sin atributo running | GET | 200 o error controlado | 500 (1 ms) | FALLA |
| YURA-EXT-605 | web | /api/status con HTML/<script> en content | <script>alert('x')</script><img src=x onerror=alert(1)> | JSON válido; la página lo pinta como texto (textContent) | 200; JSON devuelve el texto tal cual; app.js usa textContent (líneas 175-182) -> no se ejecuta (0 ms) | OK |
| YURA-EXT-606 | web | /api/status con content de 1 MB | 1.048.576 caracteres 'Ñ' | limitar tamaño | 200 respuesta=6291702 bytes en 12 ms (sin límite de tamaño) (0 ms) | OBSERVACION |
| YURA-EXT-610 | web | GET /no-existe | /no-existe | 404/405 sin filtrar información | 404 (0 ms) | OK |
| YURA-EXT-611 | web | GET /api/status/../../etc/passwd | /api/status/../../etc/passwd | 404/405 sin filtrar información | 404 (0 ms) | OK |
| YURA-EXT-612 | web | POST /api/status | /api/status | 404/405 sin filtrar información | 405 (0 ms) | OK |
| YURA-EXT-613 | web | DELETE /api/card | /api/card | 404/405 sin filtrar información | 405 (0 ms) | OK |
| YURA-EXT-614 | web | PUT / | / | 404/405 sin filtrar información | 405 (0 ms) | OK |
| YURA-EXT-620 | web | 1.000 peticiones seguidas a /api/status | 1000 x GET | todas 200; sin límite de frecuencia es observación | códigos={200} total=0.21s (0.2084 ms por petición) (0 ms) | OK |
| YURA-EXT-621 | web | 1.000 peticiones en 10 hilos + escritor concurrente | 10x100 GET + 2000 _set_web_status | sin errores | errores=0 tiempo=0.25s (0 ms) | OK |
| YURA-EXT-630 | web | Cabeceras de seguridad en GET / | GET / | CSP, nosniff, X-Frame-Options, Referrer-Policy | 200 faltan=['content-security-policy', 'x-content-type-options', 'x-frame-options', 'referrer-policy'] (0 ms) | OBSERVACION |
| YURA-EXT-631 | web | Cache-Control en /api/status | GET | no-store | Cache-Control=None (0 ms) | OBSERVACION |
