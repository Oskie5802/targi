#!/bin/bash
# =============================================================================
# START_GAME.SH – Klient Gry Targi (Debian Linux)
# Otwiera grę w Chromium z odpowiednimi flagami dla kamery i HTTPS
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVER_IP="${1:-192.168.55.101}"  # Podaj IP serwera jako argument, np: ./start_game.sh 192.168.0.10
SERVER_URL="https://${SERVER_IP}:5001"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  TARGI GAME CLIENT – Debian Edition  ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Serwer: ${YELLOW}${SERVER_URL}${NC}"
echo ""

# --- Sprawdź czy serwer odpowiada ---
echo -n "Sprawdzam połączenie z serwerem... "
if curl -sk --max-time 3 "${SERVER_URL}/" > /dev/null 2>&1; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${YELLOW}Brak odpowiedzi (serwer może być wyłączony lub certyfikat SSL niezaufany)${NC}"
fi

# --- Znajdź Chromium ---
BROWSER=""
for b in chromium chromium-browser google-chrome google-chrome-stable; do
    if command -v "$b" &> /dev/null; then
        BROWSER="$b"
        break
    fi
done

if [ -z "$BROWSER" ]; then
    echo -e "${YELLOW}Nie znaleziono Chromium/Chrome. Instaluję chromium...${NC}"
    sudo apt-get install -y chromium
    BROWSER="chromium"
fi

echo -e "${GREEN}[OK]${NC} Przeglądarka: $BROWSER"
echo ""
echo "Otwieranie gry..."
echo -e "${YELLOW}UWAGA: Przy pierwszym uruchomieniu kliknij 'Zaawansowane' → 'Przejdź mimo to'${NC}"
echo -e "${YELLOW}       (certyfikat self-signed – wystarczy raz zaakceptować)${NC}"
echo ""

# Flagi Chromium dla optymalnej wydajności gry:
# --use-gl=desktop           → OpenGL sprzętowy (lepszy rendering Three.js)
# --enable-accelerated-video-decode → Sprzętowe dekodowanie video
# --ignore-certificate-errors → Akceptuj self-signed SSL (serwer lokalny)
# --camera-access             → Pozwól na dostęp do kamery bez dodatkowych promptów
# --app                       → Tryb "app" bez paska przeglądarki (fullscreen feel)
# --start-fullscreen          → Pełny ekran

exec "$BROWSER" \
    --use-gl=desktop \
    --enable-accelerated-video-decode \
    --enable-accelerated-2d-canvas \
    --ignore-certificate-errors \
    --ignore-certificate-errors-spki-list \
    --disable-web-security \
    --allow-running-insecure-content \
    --use-fake-ui-for-media-stream=false \
    --app="${SERVER_URL}/" \
    --start-fullscreen \
    --kiosk \
    2>/dev/null &

echo -e "${GREEN}Gra uruchomiona!${NC}"
