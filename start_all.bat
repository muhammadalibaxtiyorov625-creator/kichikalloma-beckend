@echo off
title Kichik Alloma - Barcha Xizmatlar Launcher
echo ===================================================
echo   KICHIK ALLOMA - BARCHA XIZMATLARNI ISHGA TUSHIRISH
echo ===================================================

echo [1/3] Backend API server ishga tushirilmoqda (Port 3000)...
start "Kichik Alloma Backend (Port 3000)" cmd /k "cd /d c:\Users\user\Desktop\kichikalloma-beckend && python -m uvicorn main:app --host 0.0.0.0 --port 3000 --reload"
timeout /t 2 /nobreak >nul

echo [2/3] Admin Panel ishga tushirilmoqda (Port 8080)...
start "Kichik Alloma Admin Panel (Port 8080)" cmd /k "cd /d C:\Users\user\Desktop\kichikalloma-admin && python -m http.server 8080"
timeout /t 1 /nobreak >nul

echo [3/3] Asosiy Web Sayt ishga tushirilmoqda (Port 8000)...
start "Kichik Alloma Web Sayt (Port 8000)" cmd /k "cd /d C:\Users\user\Desktop\kichikalloma-website && python -m http.server 8000"
timeout /t 1 /nobreak >nul

start http://localhost:8000
start http://localhost:8080
start http://localhost:3000/docs

echo.
echo ===================================================
echo [OK] Barcha xizmatlar muvaffaqiyatli ishga tushirildi!
echo ===================================================
echo - Asosiy Web Sayt:  http://localhost:8000
echo - Admin Panel:      http://localhost:8080
echo - Backend API:      http://localhost:3000
echo - Swagger Docs:     http://localhost:3000/docs
echo.
pause
