#!/bin/bash
# =============================================================================
# START_SERVER.SH – Serwer Targi (Debian Linux)
# Uruchamia serwer Flask + sprawdza/instaluje wszystkie zależności
# =============================================================================

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  TARGI GAME SERVER – Debian Edition  ${NC}"
echo -e "${GREEN}========================================${NC}"

# --- 1. Sprawdź Python 3 ---
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR] Python3 nie znaleziony! Zainstaluj: sudo apt install python3 python3-pip python3-venv${NC}"
    exit 1
fi
echo -e "${GREEN}[OK]${NC} Python3: $(python3 --version)"

# --- 2. Sprawdź FFmpeg ---
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${YELLOW}[INFO] FFmpeg nie znaleziony. Instaling...${NC}"
    sudo apt-get update -qq && sudo apt-get install -y ffmpeg
fi
echo -e "${GREEN}[OK]${NC} FFmpeg: $(ffmpeg -version 2>&1 | head -1)"

# --- 3. Sprawdź OpenSSL (do certyfikatów SSL) ---
if ! command -v openssl &> /dev/null; then
    echo -e "${YELLOW}[INFO] OpenSSL nie znaleziony. Installing...${NC}"
    sudo apt-get install -y openssl
fi
echo -e "${GREEN}[OK]${NC} OpenSSL: $(openssl version)"

# --- 4. Wirtualne środowisko Python ---
VENV_DIR="../../venv"

if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}[INFO] Tworzenie wirtualnego środowiska Python...${NC}"
    python3 -m venv "$VENV_DIR"
fi

PYTHON="$VENV_DIR/bin/python"
PIP="$VENV_DIR/bin/pip"

echo -e "${YELLOW}[INFO] Instaluję/aktualizuję pakiety Python...${NC}"
"$PIP" install --quiet --upgrade pip
"$PIP" install --quiet flask pyopenssl

echo -e "${GREEN}[OK]${NC} Pakiety Python zainstalowane"

# --- 5. Sprawdź akcelerację sprzętową VAAPI (opcjonalne) ---
if [ -e /dev/dri/renderD128 ]; then
    echo -e "${GREEN}[GPU]${NC} Znaleziono /dev/dri/renderD128 – VAAPI dostępne"
    # Upewnij się że użytkownik ma dostęp do GPU
    if ! groups | grep -q 'video\|render'; then
        echo -e "${YELLOW}[WARN] Dodaj użytkownika do grupy 'video' lub 'render' dla VAAPI:${NC}"
        echo -e "       sudo usermod -aG video,render \$USER && newgrp video"
    fi
    # Zainstaluj libva-drm jeśli potrzeba
    if command -v vainfo &> /dev/null; then
        echo -e "${GREEN}[GPU]${NC} VAAPI info: $(vainfo 2>&1 | grep 'VAProfileH264' | head -1 | xargs)"
    fi
else
    echo -e "${YELLOW}[GPU]${NC} Brak /dev/dri/renderD128 – używam software encoder (libx264)"
fi

# --- 6. Uruchom serwer ---
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Uruchamianie serwera...              ${NC}"
echo -e "${GREEN}  Gra:         https://$(hostname -I | awk '{print $1}'):5001${NC}"
echo -e "${GREEN}  Leaderboard: https://$(hostname -I | awk '{print $1}'):5001/leaderboard${NC}"
echo -e "${GREEN}  Dashboard:   https://$(hostname -I | awk '{print $1}'):5001/dashboard${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

exec "$PYTHON" server.py
