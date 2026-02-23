# SETUP – Targi Game System

## Architektura

```
[Debian – Server + Klient Gry]  ←──LAN──→  [Windows 10 – Leaderboard]
  Flask server:5001                            Monitor 1 (Wyniki): https://IP:5001/leaderboard1
  Chromium (gra) → localhost:5001/             Monitor 2 (Kamera): https://IP:5001/leaderboard2
  FFmpeg (nagrywanie)
  MediaPipe (kamera)
```

---

## 1. Debian – Instalacja jednorazowa

```bash
# Zainstaluj podstawowe pakiety systemowe
sudo apt update
sudo apt install -y python3 python3-pip python3-venv ffmpeg openssl chromium

# (Opcjonalnie) VAAPI – sprzętowe kodowanie GPU dla Intel/AMD
sudo apt install -y vainfo libva-drm2 i965-va-driver  # Intel
# lub
sudo apt install -y mesa-va-drivers                    # AMD
sudo usermod -aG video,render $USER  # Wyloguj się i zaloguj ponownie
```

## 2. Debian – Uruchomienie serwera

```bash
cd /ścieżka/do/Ptak/
chmod +x start_server.sh
./start_server.sh
```

Serwer działa na `https://0.0.0.0:5001`.  
Przy pierwszym uruchomieniu automatycznie generuje certyfikat SSL (`ssl_cert.pem`).

## 3. Debian – Uruchomienie klienta gry

```bash
chmod +x start_game.sh
./start_game.sh          # IP serwera to 192.168.55.101 (domyślnie)
./start_game.sh 10.0.0.5  # lub podaj własne IP
```

Chromium otwiera się w trybie **kiosk/fullscreen**.  
Akceptacja certyfikatu jest automatyczna (`--ignore-certificate-errors`).

---

## 4. Windows 10 – Leaderboard (jednorazowa konfiguracja)

### Krok 1: Zaakceptuj certyfikat SSL w Chrome/Edge

1. Otwórz Chrome lub Edge na Windows 10
2. Wejdź na monitorze 1: `https://192.168.55.101:5001/leaderboard1`
3. Wejdź na monitorze 2: `https://192.168.55.101:5001/leaderboard2`
4. Kliknij w przeglądarce **"Zaawansowane"** → **"Przejdź do 192.168.55.101 (niebezpieczne)"**
4. Od teraz Chrome zapamiętuje certyfikat – nie pyta ponownie

> Certyfikat jest ważny **10 lat** i zawiera IP serwera w SAN (Subject Alternative Name),  
> więc Chrome nie pokazuje ostrzeżenia o niezgodności domeny.

### Krok 2 (opcjonalnie): Dodaj certyfikat do zaufanych Windows

Jeśli chcesz całkowicie usunąć ostrzeżenia:

1. Na Debianie (serwerze) skopiuj plik `ssl_cert.pem` na pendrive lub przez sieć
2. Na Windows 10: zmień rozszerzenie na `.crt` (np. `ssl_cert.crt`)
3. Kliknij dwukrotnie → **Instaluj certyfikat** → **Lokalny komputer**  
   → **Umieść wszystkie certyfikaty w następującym magazynie** → **Zaufane główne urzędy certyfikacji**
4. Restart Chrome/Edge

### Skrót do leaderboardu (Windows 10)

Stwórz plik `leaderboard.bat` na pulpicie:
Stwórz dwa osobne pliki na pulpicie dla obu monitorów:

**`monitor1-wyniki.bat`**:
```batch
@echo off
start chrome.exe --start-fullscreen --window-position=0,0 "https://192.168.55.101:5001/leaderboard1"
```

**`monitor2-kamera.bat`**:
```batch
@echo off
start chrome.exe --start-fullscreen --window-position=1080,0 "https://192.168.55.101:5001/leaderboard2"
```

*(Dostosuj współrzędne w `--window-position` zależnie od fizycznego układu monitorów na komputerze Windows 10)*

---

## 5. Wymagane pasmo sieciowe

| Stream | Rozdzielczość | FPS | ~Pasmo |
|--------|--------------|-----|--------|
| Kamera (live preview / nagrywanie) | 1280×720 | 60 | ~20–50 Mbps |
| Gra (stream na dashboard) | 854×480 | 30 | ~5–10 Mbps |
| **Łącznie** | | | **~25–60 Mbps** |

**Wymagane minimum:** Switch LAN **Fast Ethernet (100 Mbps)** – wystarczy.  
**Zalecane:** Switch LAN **Gigabit (1000 Mbps)** – pełen komfort.  
**WiFi:** minimum **WiFi 5 (802.11ac)** na paśmie 5GHz.

---

## 6. Diagnostyka

### Sprawdź czy FFmpeg używa GPU (VAAPI)
```bash
# Na serwerze Debian:
vainfo  # Powinno pokazać VAProfileH264Main, VAProfileH264High
ls /dev/dri/  # Powinno być renderD128
```

### Sprawdź użycie CPU podczas nagrywania
```bash
htop  # VAAPI = FFmpeg ~5-10% CPU, libx264 ultrafast = ~30-60% CPU
```

### Logi serwera
Serwer wypisuje:
```
[FFmpeg] Using VAAPI hardware encoder (/dev/dri/renderD128)
[Recorder] Started: uploads/rec_1234567890_abcd1234.mp4 (encoder: vaapi)
[Recorder] Stopped, file saved: rec_1234567890_abcd1234.mp4
```
