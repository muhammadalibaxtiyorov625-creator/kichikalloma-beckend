#!/bin/bash
set -e

DIR="/var/www/kichik-alloma"
cd "$DIR"

echo "=========================================="
echo "🛑 1. Eski jarayonlar to'xtatilmoqda..."
echo "=========================================="
sudo systemctl stop kichik-alloma 2>/dev/null || true
sudo fuser -k 3000/tcp 8000/tcp 2>/dev/null || true
sudo pkill -9 -f "uvicorn" 2>/dev/null || true

echo "=========================================="
echo "🚀 2. Tizim paketlari o'rnatilmoqda..."
echo "=========================================="
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git psmisc

echo "=========================================="
echo "🐍 3. Python kutubxonalari o'rnatilmoqda..."
echo "=========================================="
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

echo "=========================================="
echo "⚙️ 4. Systemd xizmati sozlanmoqda (Port: 3000)..."
echo "=========================================="
sudo cp kichik-alloma.service /etc/systemd/system/kichik-alloma.service
sudo systemctl daemon-reload
sudo systemctl enable kichik-alloma
sudo systemctl start kichik-alloma

sleep 2

echo "=========================================="
echo "🌐 5. Nginx (Port 80) sozlanmoqda..."
echo "=========================================="
sudo apt install -y nginx
if [ -f "/etc/nginx/sites-available/default" ]; then
    sudo bash -c 'cat > /etc/nginx/sites-available/default << "EOF"
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    client_max_body_size 100M;
    add_header Permissions-Policy "unload=*" always;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
    }
}
EOF'
    sudo nginx -t && sudo systemctl restart nginx
fi

echo "=========================================="
echo "🔍 6. Tizim holati tekshirilmoqda..."
echo "=========================================="
sudo systemctl status kichik-alloma --no-pager

echo ""
echo "=========================================="
echo "✅ Barcha xizmatlar 100% muvaffaqiyatli ishga tushdi!"
echo "Asosiy Web Sayt (Port 80):  http://189.74.97.98/"
echo "Admin Panel (Port 80):      http://189.74.97.98/admin"
echo "API Hujjatlari (Port 80):   http://189.74.97.98/docs"
echo "To'g'ridan-to'g'ri Port 3000: http://189.74.97.98:3000/"
echo "=========================================="
