@echo off
echo ========================================
echo INSTALOWANIE WYMAGANYCH BIBLIOTEK...
echo ========================================
pip install flask

echo.
echo ========================================
echo URUCHAMIANIE SERWERA GRY...
echo ========================================
start http://localhost:5000
python server.py
pause
