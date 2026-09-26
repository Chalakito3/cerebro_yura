#!/bin/sh

set -eu

url="http://yura.local:5000/"
status_url="${url}api/status"
max_attempts=180
attempt=0

browser_bin=""
for candidate in \
    /usr/bin/google-chrome \
    /usr/bin/google-chrome-stable \
    /usr/bin/chromium \
    /usr/bin/chromium-browser \
    /snap/bin/chromium; do
    if [ -x "$candidate" ]; then
        browser_bin="$candidate"
        break
    fi
done

if [ -z "$browser_bin" ]; then
    echo "[YURA] No se encontró Chrome/Chromium para la pantalla completa." >&2
    exit 1
fi

while [ "$attempt" -lt "$max_attempts" ]; do
    if /usr/bin/python3 -c 'import sys; from urllib.request import urlopen; response = urlopen(sys.argv[1], timeout=2); response.read(1)' "$status_url" >/dev/null 2>&1; then
        exec "$browser_bin" \
            --user-data-dir=/tmp/yura-kiosk \
            --no-first-run \
            --disable-infobars \
            --disable-session-crashed-bubble \
            --disable-component-update \
            --disable-features=TranslateUI,BackForwardCache,MediaRouter \
            --kiosk \
            --app="$url"
    fi
    attempt=$((attempt + 1))
    sleep 1
done

exit 1
