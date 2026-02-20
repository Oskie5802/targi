@echo off
echo ========================================
echo INSTALOWANIE WYMAGANYCH BIBLIOTEK...
echo ========================================
pip install flask pyopenssl

echo.
echo ========================================
echo URUCHAMIANIE SERWERA GRY...
echo ========================================
start https://192.168.55.101:5001
python server.py
pause
