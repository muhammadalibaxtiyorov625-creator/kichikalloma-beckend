@echo off
title Kichik Alloma - Backend & Admin Panel Launcher
echo ===================================================
echo   KICHIK ALLOMA - BARCHA XIZMATLARNI ISHGA TUSHIRISH
echo ===================================================
start "Kichik Alloma Backend (Port 3000)" cmd /k "cd /d c:\Users\user\Desktop\kichikalloma-beckend && python -m uvicorn main:app --host 0.0.0.0 --port 3000 --reload"
timeout /t 2 /nobreak >nul
start "Kichik Alloma Admin Panel (Port 8080)" cmd /k "cd /d C:\Users\user\Desktop\kichikalloma-admin && python -m http.server 8080"
timeout /t 1 /nobreak >nul
start http://localhost:8080
start http://localhost:3000/docs
echo.
echo [OK] Barcha xizmatlar muvaffaqiyatli ishga tushirildi!
echo Backend:       http://localhost:3000
echo Admin Panel:   http://localhost:8080
echo API Docs:      http://localhost:3000/docs
echo Backend Admin: http://localhost:3000/admin
echo.
pause
