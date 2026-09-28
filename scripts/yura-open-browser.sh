#!/bin/sh
# Abre la pantalla de Yura en Firefox a pantalla completa cuando el cerebro
# ya responde. Se ejecuta al iniciar sesión (scripts/yura.desktop).
# Para salir de la pantalla completa: Alt+F4.

set -eu

url="http://localhost:5000/"
status_url="${url}api/status"
max_attempts=180
attempt=0

if ! command -v firefox >/dev/null 2>&1; then
    echo "[YURA] No se encontró Firefox para la pantalla completa." >&2
    exit 1
fi

while [ "$attempt" -lt "$max_attempts" ]; do
    if /usr/bin/python3 -c 'import sys; from urllib.request import urlopen; urlopen(sys.argv[1], timeout=2).read(1)' "$status_url" >/dev/null 2>&1; then
        exec firefox --kiosk "$url"
    fi
    attempt=$((attempt + 1))
    sleep 1
done

echo "[YURA] El cerebro no respondió en ${max_attempts} s; no se abre la pantalla." >&2
exit 1
