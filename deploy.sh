#!/bin/bash
# Qo'lda tezkor yangilash skripti (Serverda ishga tushirish uchun)

set -e

echo "🚀 Yangi versiya tortilmoqda..."
git pull

echo "📦 Konteynerlar qayta qurilmoqda..."
docker compose down
docker compose up -d --build

echo "🧹 Eski keraksiz tasvirlar tozalanmoqda..."
docker image prune -f

echo "✅ Loyiha muvaffaqiyatli yangilandi!"
