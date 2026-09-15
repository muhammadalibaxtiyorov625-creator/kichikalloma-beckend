# Kichik Alloma — Mustaqil 3 Ta Bo'limdan Iborat Tizim

Ushbu loyiha 3 ta to'liq mustaqil, bir-biriga bog'lanmagan papkaga ajratilgan:

```
kichikalloma/
├── beckend/       # 🚀 REST API Server (Python FastAPI, SQLite, Media)
├── website/       # 🌐 Tashrif buyuruvchilar Web Sayti (Frontend: HTML, CSS, JS)
└── admin/         # 🛡️ Mustaqil Admin Boshqaruv Paneli (Frontend: HTML, CSS, JS)
```

---

## 1. 🚀 Backend (`beckend/`)
Faqat toza REST API beruvchi mustaqil server:
- **Papka:** `beckend/`
- **Texnologiya:** Python FastAPI, SQLite, Pydantic, JWT
- **Port:** `3000` (http://127.0.0.1:3000)
- **Ishga tushirish:**
  ```cmd
  cd beckend
  run.bat
  ```
  yoki:
  ```bash
  python -m uvicorn main:app --host 127.0.0.1 --port 3000 --reload
  ```
- **API Hujjatlari (Swagger):** `http://127.0.0.1:3000/docs`
- **Xususiyatlar:** To'liq CORS ruxsati faol, mobil ilova, sayt va admin paneldan so'rovlarni qabul qiladi.

---

## 2. 🌐 Web Sayt (`website/`)
Asosiy foydalanuvchilar va ota-onalar uchun landing sahifa:
- **Papka:** `website/`
- **Texnologiya:** Sof HTML, CSS, JavaScript (Karusellar, video pleyer, animatsiyalar)
- **Port:** `8000` (http://localhost:8000)
- **Ishga tushirish:**
  ```cmd
  cd website
  run_website.bat
  ```
  yoki:
  ```bash
  python -m http.server 8000
  ```
- **API ulash:** `website/script.js` ichidagi `getApiBaseUrl()` orqali backend manzilini oladi (`window.API_BASE_URL` yoki default `http://127.0.0.1:3000`).

---

## 3. 🛡️ Admin Panel (`admin/`)
Tizim kontentini boshqarish uchun mustaqil admin paneli:
- **Papka:** `admin/`
- **Texnologiya:** Dashboard, 3D Sayyoralar, Jamoa, Galereya, Kelgan xabarlar (Toshkent vaqti bilan)
- **Port:** `8080` (http://localhost:8080)
- **Ishga tushirish:**
  ```cmd
  cd admin
  run_admin.bat
  ```
  yoki:
  ```bash
  python -m http.server 8080
  ```
- **API ulash:** `admin/js/app.js` dagi global `API_BASE_URL` orqali xohlagan backend server manziliga ulanadi (default: `http://127.0.0.1:3000`).
- **Kirish:** Email: `kichikalloma@gmail.com`, Parol: `KichikAlloma9765100`
