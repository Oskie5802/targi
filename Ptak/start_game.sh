#!/bin/bash
# =============================================================================
# START_GAME.SH – Klient Gry Targi (Debian Linux)
# Otwiera gre w Chromium z odpowiednimi flagami dla kamery i HTTPS
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVER_IP="${1:-localhost}"  # Podaj IP serwera jako argument (domyslnie localhost bo z tej samej maszyny)
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

# --- Sprawdz czy serwer odpowiada ---
echo -n "Sprawdzam polaczenie z serwerem... "
if curl -sk --max-time 3 "${SERVER_URL}/" > /dev/null 2>&1; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${YELLOW}Brak odpowiedzi (serwer moze byc wylaczony lub certyfikat SSL niezaufany)${NC}"
fi

# --- Znajdz Chromium ---
BROWSER=""
for b in chromium chromium-browser google-chrome google-chrome-stable; do
    if command -v "$b" &> /dev/null; then
        BROWSER="$b"
        break
    fi
done

if [ -z "$BROWSER" ]; then
    echo -e "${YELLOW}Nie znaleziono Chromium/Chrome. Instaluje chromium...${NC}"
    sudo apt-get install -y chromium
    BROWSER="chromium"
fi

echo -e "${GREEN}[OK]${NC} Przegladarka: $BROWSER"
echo ""
echo "Otwieranie gry..."
echo -e "${YELLOW}UWAGA: Przy pierwszym uruchomieniu kliknij 'Zaawansowane' → 'Przejdz mimo to'${NC}"
echo -e "${YELLOW}       (certyfikat self-signed – wystarczy raz zaakceptowac)${NC}"
echo ""

# Flagi Chromium dla optymalnej wydajnosci gry:
# --use-gl=desktop           → OpenGL sprzetowy (lepszy rendering Three.js)
# --enable-accelerated-video-decode → Sprzetowe dekodowanie video
# --ignore-certificate-errors → Akceptuj self-signed SSL (serwer lokalny)
# --camera-access             → Pozwol na dostep do kamery bez dodatkowych promptow
# --app                       → Tryb "app" bez paska przegladarki (fullscreen feel)
# --start-fullscreen          → Pelny ekran

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
