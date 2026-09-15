# 🚀 Serverga Joylashtirish (Deployment) va Boshqa Serverlarga Ulash Qo'llanmasi

Ushbu qo'llanma orqali siz **Kichik Alloma** loyihasini istalgan Linux (Ubuntu / Debian / CentOS / VPS) serveriga 5 daqiqada o'rnatishingiz va GitHub Actions yordamida avtomatik serverda yangilanadigan (CI/CD) tizimini yo'lga qo'yishingiz mumkin.

Repozitoriya: **`https://github.com/muhammadalibaxtiyorov625-creator/kichikalloma.git`**

---

## 📑 Mundarija
1. [1-Usul: Docker Compose orqali (Eng qulay va xavfsiz)](#1-usul-docker-compose-orqali)
2. [2-Usul: To'g'ridan-to'g'ri VPS da (Docker siz - Systemd bilan)](#2-usul-togridan-togri-vps-da-docker-siz)
3. [Domen va Bepul SSL (HTTPS) Ulash](#domen-va-bepul-ssl-https-ulash)
4. [GitHub Actions CI/CD Avtomatik Yangilanish](#github-actions-cicd-avtomatik-yangilanish)
5. [Foydali buyruqlar va boshqaruv](#foydali-buyruqlar-va-boshqaruv)

---

## 1-Usul: Docker Compose orqali (Tavsiya etiladi)

### 1. Serveringizga SSH orqali kiring:
```bash
ssh root@SIZNING_SERVER_IP
```

### 2. Loyihani yuklab oling:
```bash
git clone https://github.com/muhammadalibaxtiyorov625-creator/kichikalloma.git /var/www/kichik-alloma
cd /var/www/kichik-alloma
```

### 3. Muhit o'zgaruvchilari faylini (`.env`) tayyorlang:
```bash
cp .env.example .env
```

### 4. Docker orqali ishga tushiring:
```bash
docker compose up -d --build
```

---

## 2-Usul: To'g'ridan-to'g'ri VPS da (Docker siz)

Agar serveringizda Docker bo'lmasa yoki resurs tejamkor bo'lishi kerak bo'lsa:

```bash
git clone https://github.com/muhammadalibaxtiyorov625-creator/kichikalloma.git /var/www/kichik-alloma
cd /var/www/kichik-alloma
chmod +x start_standalone.sh
./start_standalone.sh
```
Ushbu skript avtomatik tarzda:
- Python virtual muhitini (`venv`) yaratadi
- Frontendni `vite build` qiladi
- `kichik-alloma.service` systemd xizmatini yoqadi va server har safar qayta o'chib-yonsa ham avtomatik ishga tushadi!

---


Endi loyiha serveringizda ishlayapti:
- **Web sayt:** `http://SIZNING_SERVER_IP:3000` yoki `http://SIZNING_SERVER_IP`
- **Admin Panel:** `http://SIZNING_SERVER_IP:3000/admin`
- **Swagger Docs:** `http://SIZNING_SERVER_IP:3000/docs`

---

## 3-Qadam: Domen va SSL (HTTPS) ulash

Agar domeningiz bo'lsa (masalan: `alloma.uz` va `khv.alloma.uz`):

1. Domeningiz DNS sozlamalariga quyidagi **A-record**larni qo'shing:
   - `@` -> `SIZNING_SERVER_IP`
   - `khv` -> `SIZNING_SERVER_IP`
   - `admin` -> `SIZNING_SERVER_IP`

2. Bepul Let's Encrypt SSL sertifikatini olish:
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d alloma.uz -d khv.alloma.uz -d admin.alloma.uz
```

---

## 4-Qadam: GitHub Actions CI/CD ni yoqish (Avtomatik Deploy)

Siz GitHub ga har safar yangi kod `push` qilganingizda, serveringizdagi loyiha hech qanday qo'l aralashuvisiz avtomatik yangilanadi!

### 1. SSH kalit yaratish (Serverda):
Serveringizda:
```bash
ssh-keygen -t rsa -b 4096 -C "github-actions-deploy" -f ~/.ssh/github_deploy -N ""
cat ~/.ssh/github_deploy.pub >> ~/.ssh/authorized_keys
cat ~/.ssh/github_deploy
```
Ekranda chiqqan **Private Key** (`-----BEGIN OPENSSH PRIVATE KEY-----` dan `-----END OPENSSH PRIVATE KEY-----` gacha) ni nusxalab oling.

### 2. GitHub Secrets ga qo'shish:
GitHub repozitoriyangizga kiring:
👉 **Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret**:

Quyidagi 4 ta sirli kalitni (Secrets) qo'shing:

| Secret Nomi | Qiymati | Izoh |
|---|---|---|
| `SERVER_HOST` | `194.163.xxx.xxx` | Serveringizning IP manzili |
| `SERVER_USER` | `root` yoki `ubuntu` | Server foydalanuvchi nomi |
| `SERVER_SSH_KEY` | `-----BEGIN OPENSSH PRIVATE KEY...` | Yuqorida nusxalangan SSH kalit |
| `SERVER_PORT` | `22` | SSH porti |
| `SERVER_PROJECT_PATH` | `/var/www/kichik-alloma` | Loyiha joylashgan papka yo'li |

Endi har safar:
```bash
git add .
git commit -m "Yangi imkoniyat qo'shildi"
git push origin main
```
qilganingizda, **GitHub Actions** avtomatik ishga tushadi va serveringizdagi loyihani 1 daqiqa ichida yangilab qo'yadi!

---

## 🛠️ Foydali buyruqlar va boshqaruv

- **Loglarni jonli ko'rish:**
  ```bash
  docker compose logs -f app
  ```
- **Konteynerlar holatini tekshirish:**
  ```bash
  docker compose ps
  ```
- **Qo'lda yangilash (agar CI/CD ishlatilmasa):**
  ```bash
  ./deploy.sh
  ```
- **Serverni qayta ishga tushirish:**
  ```bash
  docker compose restart
  ```
- **Ma'lumotlar bazasini zaxira qilish (Backup):**
  ```bash
  cp /var/www/kichik-alloma/database.sqlite /var/backups/database_backup_$(date +%F).sqlite
  ```
