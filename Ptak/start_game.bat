@echo off
echo ========================================
echo INSTALOWANIE WYMAGANYCH BIBLIOTEK...
echo ========================================
pip install flask pyopenssl

echo.
echo ========================================
echo URUCHAMIANIE SERWERA GRY...
echo ========================================
start https://localhost:5001
python server.py
pause
