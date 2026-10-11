#!/bin/sh
# Abre la pantalla de Yura a pantalla completa cuando el cerebro ya responde.
# Se ejecuta al iniciar sesión (scripts/yura.desktop).
# Para salir de la pantalla completa: Alt+F4.
#
# Usa Firefox si está (como "firefox" o "firefox-esr", el nombre en
# Debian/Raspberry Pi OS); si no, Chromium (el navegador por defecto de
# Raspberry Pi OS).

set -eu

url="http://localhost:5000/"
status_url="${url}api/status"
max_attempts=180
attempt=0

navegador=""
for candidato in firefox firefox-esr chromium-browser chromium; do
    if command -v "$candidato" >/dev/null 2>&1; then
        navegador="$candidato"
        break
    fi
done

if [ -z "$navegador" ]; then
    echo "[YURA] No se encontró un navegador (Firefox o Chromium) para la pantalla completa." >&2
    exit 1
fi

# Evita que todo se vea diminuto en TV/monitores 4K: fija 1920x1080 a 60 Hz
# en la primera salida conectada. Se puede cambiar con YURA_RESOLUCION
# (ej. YURA_RESOLUCION=1280x720@60); YURA_RESOLUCION=no la deja como está.
resolucion="${YURA_RESOLUCION:-1920x1080@60}"
if [ "$resolucion" != "no" ] && command -v wlr-randr >/dev/null 2>&1; then
    salida=$(wlr-randr 2>/dev/null | awk '/^[^ ]/ {print $1; exit}')
    if [ -n "$salida" ]; then
        wlr-randr --output "$salida" --mode "$resolucion" >/dev/null 2>&1 \
            || echo "[YURA] No se pudo fijar $resolucion en $salida." >&2
    fi
fi

while [ "$attempt" -lt "$max_attempts" ]; do
    if /usr/bin/python3 -c 'import sys; from urllib.request import urlopen; urlopen(sys.argv[1], timeout=2).read(1)' "$status_url" >/dev/null 2>&1; then
        case "$navegador" in
            chromium-browser|chromium)
                exec "$navegador" --user-data-dir="$HOME/.config/yura-kiosco" --kiosk --noerrdialogs --disable-infobars --no-first-run "$url"
                ;;
            *)
                exec "$navegador" --kiosk "$url"
                ;;
        esac
    fi
    attempt=$((attempt + 1))
    sleep 1
done

echo "[YURA] El cerebro no respondió en ${max_attempts} s; no se abre la pantalla." >&2
exit 1
