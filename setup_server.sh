#!/bin/bash
# =================================================================
# Kichik Alloma - Serverni 1-marta tayyorlash skripti (Ubuntu/Debian)
# =================================================================

set -e

echo "=========================================="
echo "🚀 Serverni sozlash boshlanmoqda..."
echo "=========================================="

# 1. Tizimni yangilash
echo "📦 1. Tizim paketlari yangilanmoqda..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl git ufw apt-transport-https ca-certificates gnupg lsb-release

# 2. Docker va Docker Compose o'rnatish
echo "🐳 2. Docker o'rnatilmoqda..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo "✅ Docker o'rnatildi!"
else
    echo "✅ Docker allaqachon mavjud."
fi

# 3. Fayrvoll sozlash
echo "🛡️ 3. Xavfsizlik (UFW Fayrvoll) sozlanmoqda..."
sudo ufw allow 22/tcp || true
sudo ufw allow 80/tcp || true
sudo ufw allow 443/tcp || true
sudo ufw allow 3000/tcp || true
sudo ufw --force enable || true

# 4. Loyiha papkasini yaratish
DEPLOY_DIR="/var/www/kichik-alloma"
echo "📁 4. Loyiha papkasi: $DEPLOY_DIR"
sudo mkdir -p $DEPLOY_DIR
sudo chown -R $USER:$USER $DEPLOY_DIR

echo "=========================================="
echo "🎉 Server tayyor!"
echo "Endi loyihani git orqali $DEPLOY_DIR papkasiga clone qiling:"
echo "git clone <REPO_URL> $DEPLOY_DIR"
echo "cd $DEPLOY_DIR"
echo "cp .env.example .env"
echo "docker compose up -d --build"
echo "=========================================="
