#!/bin/sh
# Instala el arranque automático de Yura para el usuario actual:
#  - el cerebro como servicio de usuario (systemd --user)
#  - la pantalla en Firefox al iniciar sesión
# Uso: sh scripts/instalar_arranque.sh      Desinstalar: sh scripts/instalar_arranque.sh --quitar

set -eu

scripts="$(cd "$(dirname "$0")" && pwd)"
servicios="$HOME/.config/systemd/user"
autoarranque="$HOME/.config/autostart"

if [ "${1:-}" = "--quitar" ]; then
    systemctl --user disable --now yura.service 2>/dev/null || true
    rm -f "$servicios/yura.service" "$autoarranque/yura.desktop"
    systemctl --user daemon-reload
    echo "[YURA] Arranque automático desinstalado."
    exit 0
fi

mkdir -p "$servicios" "$autoarranque"
cp "$scripts/yura.service" "$servicios/yura.service"
cp "$scripts/yura.desktop" "$autoarranque/yura.desktop"
chmod +x "$scripts/yura-open-browser.sh"

systemctl --user daemon-reload
systemctl --user enable yura.service
echo "[YURA] Arranque automático instalado. Yura se encenderá al iniciar la computadora."
