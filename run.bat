@echo off
title Kichik Alloma - Backend REST API (Standalone)
echo ===================================================
echo   KICHIK ALLOMA - BACKEND REST API
echo   Manzil: http://127.0.0.1:3000
echo   API Hujjatlar (Swagger): http://127.0.0.1:3000/docs
echo ===================================================
python -m uvicorn main:app --host 127.0.0.1 --port 3000 --reload
pause
