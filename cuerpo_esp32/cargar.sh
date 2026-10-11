#!/bin/sh
# Compila y carga el programa del cuerpo (yura_cuerpo.ino) en el ESP32 por USB.
# Uso:  sh cuerpo_esp32/cargar.sh [/dev/ttyUSB0]
set -eu
carpeta="$(cd "$(dirname "$0")" && pwd)"
arduino="$(command -v arduino-cli || echo "$HOME/.local/bin/arduino-cli")"
puerto="${1:-$(ls /dev/ttyUSB* /dev/ttyACM* 2>/dev/null | head -n 1 || true)}"
if [ -z "$puerto" ]; then
    echo "[CUERPO] No se encontró el ESP32 por USB (¿cable de datos?)." >&2
    exit 1
fi
# Yura usa el mismo puerto: se detiene mientras se carga.
yura_activa=0
if systemctl --user is-active --quiet yura; then
    yura_activa=1
    systemctl --user stop yura
fi
"$arduino" compile --fqbn esp32:esp32:esp32 "$carpeta/yura_cuerpo"
"$arduino" upload --fqbn esp32:esp32:esp32 --port "$puerto" "$carpeta/yura_cuerpo"
echo "[CUERPO] Programa cargado en $puerto."
if [ "$yura_activa" = 1 ]; then
    systemctl --user start yura
fi
