@echo off
echo ========================================
echo INSTALOWANIE WYMAGANYCH BIBLIOTEK...
echo ========================================
pip install flask pyopenssl

echo.
echo ========================================
echo URUCHAMIANIE SERWERA GRY...
echo ========================================
start https://10.10.10.10:5001
python server.py
pause
