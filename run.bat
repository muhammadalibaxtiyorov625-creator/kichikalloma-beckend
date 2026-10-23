@echo off
title Kichik Alloma - Backend REST API (Standalone)
echo ===================================================
echo   KICHIK ALLOMA - BACKEND REST API
echo   Manzil: http://localhost:3000
echo   API Hujjatlar (Swagger): http://localhost:3000/docs
echo   Admin Panel: http://localhost:3000/admin
echo ===================================================
python -m uvicorn main:app --host 0.0.0.0 --port 3000 --reload
pause
