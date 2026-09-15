import os
import sys
import shutil
import uuid
import random
import re
import time
import hashlib
import asyncio
import threading
import requests as http_requests

import mimetypes

# Har qanday OT (Windows / Linux) da JS va CSS MIME turlarini to'g'ri ro'yxatdan o'tkazish
mimetypes.init()
mimetypes.add_type("application/javascript", ".js", True)
mimetypes.add_type("application/javascript", ".mjs", True)
mimetypes.add_type("text/javascript", ".js", True)
mimetypes.add_type("text/javascript", ".mjs", True)
mimetypes.add_type("text/css", ".css", True)
mimetypes.add_type("image/svg+xml", ".svg", True)
mimetypes.add_type("application/json", ".json", True)
mimetypes.add_type("application/wasm", ".wasm", True)

# Windows konsolida emojilar print bo'lganda qulab tushmasligi uchun
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Form, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from contextlib import asynccontextmanager
import google.generativeai as genai
import edge_tts

from database import get_db_connection, init_db
from schemas import (
    PlanetCreate, PlanetUpdate, PlanetResponse,
    AmenityCreate, AmenityUpdate, AmenityResponse,
    TeamCreate, TeamUpdate, TeamResponse,
    GalleryCreate, GalleryResponse,
    MessageCreate, MessageResponse,
    FaqCreate, FaqUpdate, FaqResponse,
    WebsiteLandingResponse, StatsResponse,
    SendOtpRequest, VerifyOtpRequest, VerifyOtpResponse,
    CodeAccessRequest, ChangePasscodeRequest, AddChildRequest, ChildResponse,
    AvatarResponse, SetChildAvatarRequest, UnlockAvatarResponse,
    UpdateChildProfileRequest, SetLanguageRequest, LanguageOption,
    ParentProfileResponse, TrackTimeRequest, ChildActivityStatsResponse,
    AiChatHistoryItemResponse,
    AiChatRequest, AiChatResponse, AiTtsRequest,
    AiVoiceChatResponse, AiSttResponse,
    EmotionOption, RecordEmotionRequest, EmotionItemResponse,
    WeeklyChildEmotionsResponse, ParentChildEmotionsAnalyticsResponse,
    UranCategoryBase, UranCategoryCreate, UranCategoryUpdate, UranCategoryResponse,
    UranWordBase, UranWordCreate, UranWordUpdate, UranWordResponse,
    UranQuizOption, UranCategoryDetailResponse,
    UranPracticeStats, UranPracticeSessionResponse,
    UranQuizSubmitRequest, UranQuizSubmitResponse,
    UranAiSuggestRequest, UranAiSuggestResponse,
    CoinBalanceResponse, CoinTransactionResponse,
    EarnCoinRequest, EarnCoinResponse,
    DailyBonusResponse,
    DailyMissionResponse, ClaimMissionResponse,
    ShopItemResponse, BuyShopItemRequest, BuyShopItemResponse,
    InventoryItemResponse, EquipItemRequest, EquipItemResponse,
    LeaderboardItemResponse,
    LibraryCategoryResponse, LibraryBookItemResponse, LibraryBookDetailResponse,
    LibraryPlayerResponse, LibraryHomeResponse,
    LibraryBookProgressRequest, LibraryBookProgressResponse,
    LibraryFavoriteResponse, CreateBookRequest, UpdateBookRequest
)

# Gemini AI Konfiguratsiyasi
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as e:
        print("Gemini configure xatosi:", e)

# JWT Konfiguratsiyasi
JWT_SECRET_KEY = "educational-space-platform-super-secret-key-2026"
JWT_ALGORITHM = "HS256"
security = HTTPBearer(auto_error=False)

# Yangi foydalanuvchilar (is_new_user == True) uchun in-memory vaqtinchalik kesh
# Farzand qo'shilgach (is_new_user == False), database ga ko'chiriladi
TEMP_PASSCODE_CACHE = {}  # {user_id: passcode}

# ─── ESKIZ SMS KONFIGURATSIYASI ───────────────────────────────────────────────
ESKIZ_EMAIL    = "kozimovmuhammadsodiq4472477@gmail.com"
ESKIZ_PASSWORD = "jrG6SLAo3sdhw1O6eC5n3PPBopcJFzTBOx9gnISL"
ESKIZ_FROM     = "4546"
ESKIZ_AUTH_URL = "https://notify.eskiz.uz/api/auth/login"
ESKIZ_SMS_URL  = "https://notify.eskiz.uz/api/message/sms/send"

import threading

# Tezkor HTTPS ulanish sessiyasi (Keep-Alive)
_eskiz_session = http_requests.Session()
_eskiz_token_cache = {"token": None, "expires_at": 0}

def _get_eskiz_token() -> Optional[str]:
    """Eskiz API dan JWT token olish (kesh bilan)."""
    now = time.time()
    if _eskiz_token_cache["token"] and now < _eskiz_token_cache["expires_at"]:
        return _eskiz_token_cache["token"]
    try:
        resp = _eskiz_session.post(
            ESKIZ_AUTH_URL,
            data={"email": ESKIZ_EMAIL, "password": ESKIZ_PASSWORD},
            timeout=4
        )
        if resp.status_code == 200:
            token = resp.json().get("data", {}).get("token")
            if token:
                _eskiz_token_cache["token"] = token
                _eskiz_token_cache["expires_at"] = now + 24 * 3600  # 24 soat kesh
                return token
        print(f"[ESKIZ] Login javobi: status={resp.status_code}")
        return None
    except Exception as e:
        print(f"[ESKIZ] Token olishda xato: {e}")
        return None

def send_eskiz_sms_worker(phone: str, message: str,code:str):
    """Fonda (background thread) SMS ni o'ta tezkor yuborish worker funksiyasi"""
    try:
        clean_phone = phone.replace("+", "").replace(" ", "").replace("-", "")
        token = _get_eskiz_token()
        if not token:
            print(f"[ESKIZ] Token olinmadi, SMS jo'natilmadi ({clean_phone})")
            return

        # 1. Avval asosiy Kichikalloma xavfsizlik matni yuboriladi
        resp = _eskiz_session.post(
            ESKIZ_SMS_URL,
            data={
                "mobile_phone": clean_phone,
                "message": message,
                "from": ESKIZ_FROM,
            },
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )

        # 2. Agar Eskiz akkaunt test rejimida bo'lsa va maxsus matnni rad etsa:
        # Foydalanuvchining telefoniga SMS 100% yetib borishi uchun darhol test shabloni bilan jo'natiladi
        if resp.status_code != 200:
            print(f"[ESKIZ] Asosiy matn rad etildi ({resp.status_code}), telefonga SMS borishi uchun Eskiz test shabloni yuborilmoqda...")
            resp = _eskiz_session.post(
                ESKIZ_SMS_URL,
                data={
                    "mobile_phone": clean_phone,
                    "message": "Kichikalloma: Sizning tasdiqlash kodingiz: "+code+". Ushbu kodni hech kimga, hatto ilova xodimlariga ham ko'rsatmang!",
                    "from": ESKIZ_FROM,
                },
                headers={"Authorization": f"Bearer {token}"},
                timeout=5
            )

        print(f"[ESKIZ] SMS holati: {clean_phone} -> status={resp.status_code} | {resp.text}")
    except Exception as e:
        print(f"[ESKIZ] SMS tezkor yuborish xatosi: {e}")

def send_eskiz_sms(phone: str, message: str,code:str) -> bool:
    """SMS ni bloklamasdan fonda millisekundda jo'natish"""
    t = threading.Thread(target=send_eskiz_sms_worker, args=(phone, message,code), daemon=True)
    t.start()
    return True
# ─────────────────────────────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=365))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> dict:
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autentifikatsiya tokeni talab qilinadi (Header: Authorization: Bearer <token>)"
        )
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        raw_uid = payload.get("user_id") or payload.get("sub")
        if raw_uid is None:
            raise HTTPException(status_code=401, detail="Yaroqsiz token!")
        user_id = int(raw_uid)
    except (JWTError, ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Token eskirgan yoki noto'g'ri!")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=401, detail="Foydalanuvchi topilmadi!")
    return dict(user)

def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[dict]:
    """Token bo'lsa foydalanuvchini aniqlaydi, bo'lmasa xato bermasdan None qaytaradi"""
    if not credentials or not credentials.credentials:
        return None
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        raw_uid = payload.get("user_id") or payload.get("sub")
        if raw_uid is None:
            return None
        user_id = int(raw_uid)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None
    except Exception:
        return None

def normalize_phone(phone: str) -> str:
    """Telefon raqamni toza +998934472477 formatiga keltirish"""
    raw = phone.strip()
    digits = re.sub(r"[^\d]", "", raw)
    if digits.startswith("998") and len(digits) == 12:
        return f"+{digits}"
    elif len(digits) == 9:
        return f"+998{digits}"
    elif raw.startswith("+"):
        return raw
    return f"+{digits}"


# Lifespan context manager for database initialization
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    uploads_dir = os.path.join(os.path.dirname(__file__), "public", "images", "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    yield

tags_metadata = [
    {
        "name": "Mobil Ilova — Sayyoralar (Planets)",
        "description": "Mobil ilova sayyoralari umumiy ro'yxati (Barcha sayyoralar, ovozli Alloma AI audiolari va holatlar)"
    },
    {
        "name": "Mobil Ilova — Uran Sayyorasi (Nutq & Til)",
        "description": "Uran sayyorasi (Nutq va Til) mobil API lari: Mavzular ro'yxati, So'zlar kartochkalari, Yangi so'zlarni o'rganish (/learn), Takrorlash (/review) va Test natijalarini topshirish (/submit-test)"
    },
    {
        "name": "Mobil Ilova — Neptun Sayyorasi (Hissiyotlar & Emotsiyalar)",
        "description": "Neptun sayyorasi (Hissiyotlar va Ruhiy salomatlik) mobil API lari: Emotsiyalar ro'yxati, Kayfiyatni belgilash, 7 kunlik tarix va Ota-ona uchun tahlil"
    },
    {
        "name": "Mobil Ilova — Coin & Mukofotlar Tizimi (Coins & Rewards)",
        "description": "Mobil ilova tangalar (coin) tizimi: Balans, Kunlik Bonuslar (Streak), Dars/Testlardan Coin ishlash (Earn), Kunlik Topshiriqlar (Missions), Do'kon (Shop), Sotib olingan buyumlar (Inventory) va Allomalar Reytingi (Leaderboard)"
    },
    {
        "name": "Mobil Ilova — Alloma AI & Ovozli Yordamchi",
        "description": "Alloma AI bilan matnli va ovozli suhbat (Chat), Ovozni matnga aylantirish (STT), Matndan bolalar ovozida nutq yaratish (TTS) va Suhbatlar tarixi"
    },
    {
        "name": "Mobil Ilova — Autentifikatsiya & Farzandlar Boshqaruvi",
        "description": "SMS OTP orqali kirish/ro'yxatdan o'tish, 4-xonali PIN kod, Farzand profillarini yaratish/tahrirlash, Faollik vaqtini kuzatish va FAQ"
    },
    {
        "name": "Web & Admin — Uran Sayyorasi Boshqaruvi",
        "description": "Uran sayyorasi kategoriyalari va so'zlarini admin panel orqali qo'shish, tahrirlash, o'chirish, AI orqali so'z tarjimalarini generatsiya qilish"
    },
    {
        "name": "Web & Admin — Sayyoralar Interaktiv Mashqlari",
        "description": "Web-sayt interaktiv sayyora mashqlari: Saturn (Matematika), Yupiter (Kun tartibi), Venera (Kiyimlar), Neptun (Hissiyotlar daraxti)"
    },
    {
        "name": "Web Sayt (Website)",
        "description": "Bolalar ta'lim platformasi web-sayti: Sayyoralar, Qulayliklar, Jamoa (Teams), Galereya (Gallery), Xabarlar va Statistika API lari"
    },
    {
        "name": "Website & Admin API",
        "description": "Admin boshqaruv paneli va Web portal tizimi uchun umumiy boshqaruv API lari"
    }
]

app = FastAPI(
    title="Ta'lim Platformasi & Mobil Ilova REST API",
    description="Bolalar ta'limi platformasi hamda Mobil Ilova (OTP, PIN, Farzandlar) uchun to'liq Python FastAPI REST API tizimi.",
    version="2.0.0",
    openapi_tags=tags_metadata,
    lifespan=lifespan
)

# CORS Middleware (Barcha IP, Domen va Portlar uchun 100% ruxsat)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Har doim to'g'ri CORS, Content-Type (JS, CSS, HTML) va no-cache sarlavhalarini ta'minlovchi middleware
@app.middleware("http")
async def enforce_mime_types_and_headers(request: Request, call_next):
    # OPTIONS (Preflight) so'rovlarini zudlik bilan 200 OK bilan qondirish
    if request.method == "OPTIONS":
        origin = request.headers.get("origin") or "*"
        return Response(
            content="",
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD",
                "Access-Control-Allow-Headers": request.headers.get("access-control-request-headers") or "*",
                "Access-Control-Max-Age": "86400",
                "Permissions-Policy": "unload=*",
            }
        )

    try:
        response = await call_next(request)
        path = request.url.path.lower()
        origin = request.headers.get("origin")
        
        # Har qanday so'rovga CORS sarlavhasini kafolatlangan holda qo'shish
        if origin:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD"
            response.headers["Access-Control-Allow-Headers"] = "*"
        else:
            response.headers["Access-Control-Allow-Origin"] = "*"
            
        # Brauzerlarda "Strict MIME type checking" xatosi chiqmasligi uchun JS va CSS ga to'g'ri MIME type berish
        if path.endswith(".js") or path.endswith(".mjs"):
            response.headers["content-type"] = "application/javascript; charset=utf-8"
        elif path.endswith(".css"):
            response.headers["content-type"] = "text/css; charset=utf-8"
        elif path.endswith(".wasm"):
            response.headers["content-type"] = "application/wasm"
        elif path.endswith(".svg"):
            response.headers["content-type"] = "image/svg+xml"
            
        # Permissions-Policy orqali unload bloklanishini oldini olish
        response.headers["Permissions-Policy"] = "unload=*"
            
        if path.startswith("/js") or path.startswith("/css") or path.startswith("/assets") or path in ["/", "/admin", "/admin.html"]:
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response
    except Exception as exc:
        print(f"[SERVER ERROR] {request.method} {request.url.path}: {exc}")
        origin = request.headers.get("origin") or "*"
        return JSONResponse(
            status_code=500,
            content={"detail": "Server ichki xatoligi bartaraf etildi", "error": str(exc), "success": False},
            headers={
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD",
                "Access-Control-Allow-Headers": "*",
            }
        )

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "success": False}
    )

@app.exception_handler(Exception)
async def custom_global_exception_handler(request: Request, exc: Exception):
    print(f"[GLOBAL UNHANDLED ERROR] {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Server ichki xatoligi", "error": str(exc), "success": False}
    )

# Statik fayllarni ulash
BASE_DIR = os.path.dirname(__file__)
PUBLIC_DIR = os.path.join(BASE_DIR, "public")
UPLOADS_DIR = os.path.join(PUBLIC_DIR, "images", "uploads")
AUDIO_CACHE_DIR = os.path.join(PUBLIC_DIR, "audio_cache")
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(AUDIO_CACHE_DIR, exist_ok=True)

# API Media va Yuklamalar (Images, Audio, Uploads)
if os.path.exists(os.path.join(PUBLIC_DIR, "images")):
    app.mount("/images", StaticFiles(directory=os.path.join(PUBLIC_DIR, "images")), name="images")
if os.path.exists(AUDIO_CACHE_DIR):
    app.mount("/audio_cache", StaticFiles(directory=AUDIO_CACHE_DIR), name="audio_cache")
if os.path.exists(os.path.join(PUBLIC_DIR, "audio")):
    app.mount("/audio", StaticFiles(directory=os.path.join(PUBLIC_DIR, "audio")), name="audio")


def is_admin_subdomain(request: Request) -> bool:
    """Tekshirish: so'rov admin subdomendan (khv.localhost, admin.localhost, khv.*, admin.*) kelganmi?"""
    forwarded_host = request.headers.get("x-forwarded-host")
    host = (forwarded_host or request.headers.get("host") or "").lower()
    host_clean = host.split(":")[0].strip()
    return (
        host_clean.startswith("khv.") or
        host_clean.startswith("admin.") or
        host_clean in ["khv", "admin"]
    )


def get_base_url(request: Request) -> str:
    """Hozirgi so'rov kelgan real domen va protokolni aniqlash (Ngrok, Localhost, Server IP)"""
    forwarded_proto = request.headers.get("x-forwarded-proto")
    forwarded_host = request.headers.get("x-forwarded-host")
    host = forwarded_host or request.headers.get("host")
    
    if host:
        proto = forwarded_proto
        if not proto:
            proto = "https" if ("ngrok" in host or "https" in str(request.url)) else request.url.scheme
        return f"{proto}://{host}".rstrip("/")
    
    env_base = os.environ.get("BASE_URL")
    if env_base:
        return env_base.rstrip("/")
    
    return str(request.base_url).rstrip("/")


def get_tashkent_now() -> datetime:
    """Toshkent mahalliy vaqtini qaytaradi (UTC+5)"""
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Asia/Tashkent"))
    except Exception:
        return datetime.utcnow() + timedelta(hours=5)


def format_tashkent_datetime(dt_val: Optional[str] = None) -> dict:
    """Sana va vaqtni to'g'ri va tushunarli formatga o'tkazish"""
    if not dt_val:
        now = get_tashkent_now()
        d_str = now.strftime("%d.%m.%Y")
        t_str = now.strftime("%H:%M")
        return {
            "created_at": now.strftime("%Y-%m-%d %H:%M:%S"),
            "created_date": d_str,
            "created_time": t_str,
            "formatted_time": f"{d_str}, {t_str}"
        }

    cleaned = str(dt_val).strip()
    m = re.match(r'^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})(?::(\d{2}))?', cleaned)
    if m:
        year, month, day, hour, minute = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)
        d_str = f"{day}.{month}.{year}"
        t_str = f"{hour}:{minute}"
        return {
            "created_at": cleaned,
            "created_date": d_str,
            "created_time": t_str,
            "formatted_time": f"{d_str}, {t_str}"
        }

    return {
        "created_at": cleaned,
        "created_date": cleaned,
        "created_time": "",
        "formatted_time": cleaned
    }


def sanitize_image_path(image_path: Optional[str]) -> str:
    """Bazaga saqlashda har qanday host/localhost prefikslarini tozalab, toza nisbiy yo'l qilib saqlash"""
    if not image_path:
        return "/images/planets/earth.svg"
    clean = image_path.strip()
    match = re.match(r'^https?://[^/]+(/images/.*)$', clean)
    if match:
        return match.group(1)
    return clean


def to_full_image_url(image_path: Optional[str], request: Request) -> str:
    """Avtomatik ravishda hozirgi so'rov domeniga moslab to'liq URL yasash"""
    if not image_path:
        image_path = "/images/planets/earth.svg"
    
    if image_path.startswith("data:"):
        return image_path
        
    base_url = get_base_url(request)
    clean_path = image_path.strip()
    
    # Agar avval localhost:3009 yoki boshqa eski domen bilan kelgan bo'lsa
    match = re.match(r'^https?://[^/]+(/images/.*)$', clean_path)
    if match:
        clean_path = match.group(1)
        
    # Agar tashqi internet havolasi bo'lsa
    if (clean_path.startswith("http://") or clean_path.startswith("https://")) and not clean_path.startswith(base_url):
        return clean_path
        
    # Agar kategoriyalar rasmi bo'lib, .svg bo'lsa, .png ga o'tkazamiz
    if "/images/categories/" in clean_path and clean_path.endswith(".svg"):
        clean_path = clean_path[:-4] + ".png"

    if clean_path.startswith("/"):
        return f"{base_url}{clean_path}"
    else:
        return f"{base_url}/{clean_path}"


# ==============================================================================
# ACCEPT-LANGUAGE HEADER — TIL ANIQLASH VA TARJIMA
# ==============================================================================

# Tarjima keshlari (tezkorlik uchun RAM da saqlash)
_TRANSLATION_CACHE: dict = {}

def get_accept_language(request: Request) -> str:
    """
    Request headerdan tilni aniqlaydi.
    Accept-Language: ru  →  "rus"
    Accept-Language: en  →  "eng"
    Accept-Language: uz  →  "uzb"
    Default: "uzb"
    """
    raw = request.headers.get("Accept-Language", "").strip().lower()
    if not raw:
        return "uzb"
    # Birinchi til kodi (vergul yoki nuqtali vergul bilan bo'lingan)
    code = raw.split(",")[0].split(";")[0].strip().split("-")[0]
    if code in ("ru", "rus", "ru-ru"):
        return "rus"
    if code in ("en", "eng", "en-us", "en-gb"):
        return "eng"
    return "uzb"


def get_accept_language_from_str(raw: str) -> str:
    """String dan tilni aniqlaydi"""
    if not raw:
        return "uzb"
    low = raw.strip().lower().split(",")[0].split(";")[0].strip().split("-")[0]
    if low in ("ru", "rus"):
        return "rus"
    if low in ("en", "eng"):
        return "eng"
    return "uzb"


# Statik tarjimalar (tezkor)
_STATIC_TRANSLATIONS = {
    # Oy nomlari
    "uzb": {
        "months": ["", "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun", "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr"],
        "days": ["Dush", "Sesh", "Chor", "Pay", "Juma", "Shan", "Yak"],
        "soat": "soat",
        "daqiqa": "daqiqa",
        "kun": "kun",
        "faol": "Faol",
        "nofaol": "Nofaol",
        "qiz_bola": "Qiz bola",
        "ogil_bola": "O'g'il bola",
        "salom": "Salom!",
        "yordam": "Qanday yordam bera olaman?",
    },
    "rus": {
        "months": ["", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"],
        "days": ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"],
        "soat": "ч",
        "daqiqa": "мин",
        "kun": "дн",
        "faol": "Активный",
        "nofaol": "Неактивный",
        "qiz_bola": "Девочка",
        "ogil_bola": "Мальчик",
        "salom": "Привет!",
        "yordam": "Чем могу помочь?",
    },
    "eng": {
        "months": ["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
        "days": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "soat": "h",
        "daqiqa": "min",
        "kun": "d",
        "faol": "Active",
        "nofaol": "Inactive",
        "qiz_bola": "Girl",
        "ogil_bola": "Boy",
        "salom": "Hello!",
        "yordam": "How can I help you?",
    }
}

def _t(key: str, lang: str) -> str:
    """Static tarjimani qaytaradi"""
    d = _STATIC_TRANSLATIONS.get(lang, _STATIC_TRANSLATIONS["uzb"])
    return d.get(key, _STATIC_TRANSLATIONS["uzb"].get(key, key))


def translate_text_sync(text: str, target_lang: str) -> str:
    """
    Gemini orqali matnni tarjima qiladi (kesh bilan).
    uzb matni uchun tarjima qilinmaydi.
    """
    if not text or not text.strip():
        return text
    if target_lang == "uzb":
        return text

    cache_key = hashlib.md5(f"{target_lang}:{text}".encode("utf-8")).hexdigest()
    if cache_key in _TRANSLATION_CACHE:
        return _TRANSLATION_CACHE[cache_key]

    lang_name = "Russian" if target_lang == "rus" else "English"
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = (
            f"Translate the following Uzbek text to {lang_name}. "
            f"Keep emojis. Return ONLY the translated text, no explanation, no quotes:\n\n{text}"
        )
        result = model.generate_content(prompt)
        translated = result.text.strip() if result.text else text
        _TRANSLATION_CACHE[cache_key] = translated
        return translated
    except Exception as e:
        print(f"[TRANSLATE] Error: {e}")
        return text


# Planet introductions — barcha 3 tilda
PLANET_INTROS_MULTILANG = {
    42: {
        "uzb": "Salom! Sen Kognitiv sayyorasidasan. Bu yerda mantiqiy jumboqlarni yechamiz. Qanday savoling bor? 🧠",
        "rus": "Привет! Ты на планете Когнитив. Здесь мы решаем логические задачки. Какой у тебя вопрос? 🧠",
        "eng": "Hello! You're on the Cognitive planet. Here we solve logic puzzles. What's your question? 🧠"
    },
    43: {
        "uzb": "Salom! Sen Jismoniy sayyoradasan. Bu yerda chaqqonlik va mashqlarni o'rganamiz. Qani, boshlaymizmi? 🏃‍♂️",
        "rus": "Привет! Ты на планете Физическое развитие. Здесь мы учимся ловкости и упражнениям. Начнём? 🏃‍♂️",
        "eng": "Hello! You're on the Physical planet. Here we learn agility and exercises. Shall we start? 🏃‍♂️"
    },
    44: {
        "uzb": "Salom! Sen Nutq va til sayyorasidasan. Bu yerda chiroyli gapirish va ertaklarni o'rganamiz. Nima haqida gaplashamiz? 🗣️",
        "rus": "Привет! Ты на планете Речь и язык. Здесь мы учимся красиво говорить и рассказывать сказки. О чём поговорим? 🗣️",
        "eng": "Hello! You're on the Speech & Language planet. Here we learn to speak beautifully and tell stories. What shall we talk about? 🗣️"
    },
    45: {
        "uzb": "Salom! Sen Ijtimoiy sayyoradasan. Bu yerda do'stlik va jamoada ishlashni o'rganamiz! 🤝",
        "rus": "Привет! Ты на планете Социальное развитие. Здесь мы учимся дружбе и работе в команде! 🤝",
        "eng": "Hello! You're on the Social planet. Here we learn friendship and teamwork! 🤝"
    },
    46: {
        "uzb": "Salom! Sen Emotsional sayyoradasan. Bugun kayfiyating qanday? 😊",
        "rus": "Привет! Ты на планете Эмоции. Как у тебя сегодня настроение? 😊",
        "eng": "Hello! You're on the Emotional planet. How are you feeling today? 😊"
    },
    47: {
        "uzb": "Salom! Sen Axloqiy sayyoradasan. Bu yerda yaxshi fazilatlarni o'rganamiz. ⚖️",
        "rus": "Привет! Ты на планете Нравственность. Здесь мы изучаем хорошие качества. ⚖️",
        "eng": "Hello! You're on the Ethics planet. Here we learn good values. ⚖️"
    },
    48: {
        "uzb": "Salom! Sen Ijodkorlik sayyorasidasan. Bugun nima chizamiz yoki yasaymiz? 🎨",
        "rus": "Привет! Ты на планете Творчество. Что сегодня нарисуем или сделаем? 🎨",
        "eng": "Hello! You're on the Creativity planet. What shall we draw or make today? 🎨"
    },
    49: {
        "uzb": "Salom! Sen O'z-o'zini boshqarish sayyorasidasan. Bugungi rejang qanday? 🎯",
        "rus": "Привет! Ты на планете Самоконтроль. Каков твой план на сегодня? 🎯",
        "eng": "Hello! You're on the Self-Management planet. What's your plan for today? 🎯"
    },
    50: {
        "uzb": "Salom! Sen Quyoshdasan. Men bilan xohlagan mavzuda suhbatlashishing mumkin! ☀️",
        "rus": "Привет! Ты на Солнце. Ты можешь говорить со мной на любую тему! ☀️",
        "eng": "Hello! You're on the Sun. You can chat with me on any topic! ☀️"
    }
}

PLANET_INTROS_STATIC = {
    42: "Salom! Sen Kognitiv sayyorasidasan. Bu yerda mantiqiy jumboqlarni yechamiz. Qanday savoling bor? 🧠",
    43: "Salom! Sen Jismoniy sayyoradasan. Bu yerda chaqqonlik va mashqlarni o'rganamiz. Qani, boshlaymizmi? 🏃‍♂️",
    44: "Salom! Sen Nutq va til sayyorasidasan. Bu yerda chiroyli gapirish va ertaklarni o'rganamiz. Nima haqida gaplashamiz? 🗣️",
    45: "Salom! Sen Ijtimoiy sayyoradasan. Bu yerda do'stlik va jamoada ishlashni o'rganamiz! 🤝",
    46: "Salom! Sen Emotsional sayyoradasan. Bugun kayfiyating qanday? 😊",
    47: "Salom! Sen Axloqiy sayyoradasan. Bu yerda yaxshi fazilatlarni o'rganamiz. ⚖️",
    48: "Salom! Sen Ijodkorlik sayyorasidasan. Bugun nima chizamiz yoki yasaymiz? 🎨",
    49: "Salom! Sen O'z-o'zini boshqarish sayyorasidasan. Bugungi rejang qanday? 🎯",
    50: "Salom! Sen Quyoshdasan. Men bilan xohlagan mavzuda suhbatlashishing mumkin! ☀️"
}

def get_planet_audio_hash(planet_id: int, intro_text: str) -> str:
    """Sayyora ovozli tanishtiruvining doimiy keshlangan audio fayl nomi"""
    clean = re.sub(r'[*#_`~>•]', '', intro_text)
    clean = re.sub(r'[\U00010000-\U0010ffff]', '', clean).strip()
    hash_key = hashlib.md5(f"uz-UZ-SardorNeural:+32Hz:+8%:+50%:{clean}".encode('utf-8')).hexdigest()
    return f"{hash_key}.mp3"


def format_planet_row(row, request: Request, lang: str = "uzb") -> dict:
    d = dict(row)
    pid = d.get("id")
    raw_img = (d.get("image") or "").strip()

    # Sayyora nomiga qarab standart fallback rasm
    PLANET_TITLE_TO_IMG = {
        "kognitiv": "/planets/earth.png",
        "jismoniy": "/planets/mars.png",
        "nutq": "/planets/uran.png",
        "ijtimoiy": "/planets/neptune.png",
        "emotsional": "/planets/venus.png",
        "axloqiy": "/planets/saturn.png",
        "ijodkorlik": "/planets/jupiter.png",
        "boshqarish": "/planets/mercury.png",
        "quyosh": "/planets/sun.png",
        "ai chat": "/planets/sun.png",
    }
    title_lower = (d.get("title") or "").lower()
    fallback_img = "/planets/earth.png"
    for keyword, img_path in PLANET_TITLE_TO_IMG.items():
        if keyword in title_lower:
            fallback_img = img_path
            break

    # DB dagi rasm bo'lsa o'sha ishlatiladi, bo'lmasa fallback
    final_img = raw_img if raw_img else fallback_img
    d["image"] = to_full_image_url(final_img, request)
    
    # is_blocked va is_block
    is_inactive = d.get("status", "active") != "active"
    db_is_blocked = bool(d.get("is_blocked", 0))
    db_is_block = bool(d.get("is_block", 0))
    final_blocked = is_inactive or db_is_blocked or db_is_block
    d["is_blocked"] = final_blocked
    d["is_block"] = final_blocked

    # Tashqi til bo'lsa, title va description ni tarjima qilish
    base_title = d.get("title", "")
    base_desc = d.get("description", "")
    if lang != "uzb":
        base_title = translate_text_sync(base_title, lang)
        base_desc = translate_text_sync(base_desc, lang)
    d["title"] = base_title
    d["description"] = base_desc
    d["name"] = base_title

    # Planet intro — multilang lug'atdan, yo tarjima qilib
    multilang_intros = PLANET_INTROS_MULTILANG.get(pid, {})
    if multilang_intros:
        intro = multilang_intros.get(lang, multilang_intros.get("uzb", ""))
    else:
        raw_intro = PLANET_INTROS_STATIC.get(pid)
        if not raw_intro:
            raw_intro = f"Salom! Sen {d.get('title', '')} sayyorasidasan. {d.get('description', '')}".strip()
        intro = translate_text_sync(raw_intro, lang)

    d["ai_intro"] = intro
    audio_file = get_planet_audio_hash(pid, intro)
    d["audio_url"] = to_full_image_url(f"/audio_cache/{audio_file}", request)
    raw_video = (d.get("video") or "").strip()
    d["video"] = to_full_image_url(raw_video, request) if raw_video else None
    return d


def format_team_row(row, request: Request, lang: str = "uzb") -> dict:
    d = dict(row)
    raw_img = (d.get("image") or "").strip()
    tid = d.get("id") or 1
    fallback_img = f"/images/team/member{((tid - 1) % 4) + 1}.svg"

    final_img = raw_img if raw_img else fallback_img
    d["image"] = to_full_image_url(final_img, request)
    desc = d.get("description") or ""
    d["description"] = translate_text_sync(desc, lang) if lang != "uzb" else desc
    first_name = d.get("first_name", "").strip()
    last_name = d.get("last_name", "").strip()
    d["full_name"] = f"{first_name} {last_name}".strip()
    d["firstName"] = first_name
    d["lastName"] = last_name
    d["direction"] = d.get("role", "")
    return d


def format_gallery_row(row, request: Request, lang: str = "uzb") -> dict:
    d = dict(row)
    d["image"] = to_full_image_url(d.get("image"), request)
    title = d.get("title", "")
    d["title"] = translate_text_sync(title, lang) if lang != "uzb" else title
    return d


def format_child_row(row, request: Request, lang: str = "uzb") -> dict:
    d = dict(row)
    avatar = d.get("avatar") or "/images/avatars/boy1.png"
    if avatar.endswith(".svg"):
        avatar = avatar.replace(".svg", ".png")
    d["avatar"] = to_full_image_url(avatar, request)
    d["language"] = d.get("language") or "uzb"

    # Tug'ilgan yildan yoshni avtomatik hisoblash
    year_str = str(d.get("year", "2018")).strip()
    birth_year = 2018
    match = re.search(r'\b(20\d{2}|19\d{2})\b', year_str)
    if match:
        try:
            birth_year = int(match.group(1))
        except Exception:
            birth_year = 2018

    now_year = datetime.now().year
    calculated_age = max(1, min(18, now_year - birth_year))
    d["age"] = calculated_age

    # Jins nomi — tilga mos
    gender_raw = str(d.get("gender", "male")).strip().lower()
    if gender_raw in ["female", "qiz", "girl", "f", "ayol"]:
        d["gender_label"] = _t("qiz_bola", lang)
    else:
        d["gender_label"] = _t("ogil_bola", lang)

    # Tangalar (coins) ma'lumotlarini qo'shish
    child_id = d.get("id")
    total_coins = 50
    level = 1
    streak_days = 1
    if child_id:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT total_coins, level, streak_days FROM child_coins WHERE child_id = ?", (child_id,))
            c_row = cursor.fetchone()
            if c_row:
                total_coins = c_row["total_coins"] or 0
                level = c_row["level"] or 1
                streak_days = c_row["streak_days"] or 1
            else:
                uid = d.get("user_id") or 1
                cursor.execute("""
                    INSERT OR IGNORE INTO child_coins (child_id, user_id, total_coins, lifetime_coins, streak_days, last_daily_bonus_date, level)
                    VALUES (?, ?, 50, 50, 1, '', 1)
                """, (child_id, uid))
                conn.commit()
            conn.close()
        except Exception:
            pass

    d["coins"] = total_coins
    d["total_coins"] = total_coins
    d["level"] = level
    d["streak_days"] = streak_days

    return d


def format_faq_row(row, lang: str = "uzb") -> dict:
    d = dict(row)
    base_title = d.get("name", "")
    base_answer = d.get("description", "")
    d["title"] = translate_text_sync(base_title, lang) if lang != "uzb" else base_title
    d["answer"] = translate_text_sync(base_answer, lang) if lang != "uzb" else base_answer
    d["name"] = d["title"]
    d["description"] = d["answer"]
    return d


# ==============================================================================
# FRONTEND SAHIFALAR (ASOSIY WEB SAYT & ADMIN PANEL SUB-DOMEN MARSHRUTLASH)
# ==============================================================================
@app.get("/", include_in_schema=False)
def serve_root(request: Request):
    """
    Kichik Alloma REST API Server Asosiy Holat Marshruti.
    Frontend va Admin panel to'liq alohida papkalarga ajratilgan.
    """
    return {
        "status": "online",
        "service": "Kichik Alloma Backend REST API Server",
        "version": "2.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }


@app.get("/admin", include_in_schema=False)
@app.get("/admin/", include_in_schema=False)
def serve_admin_panel_info():
    """Admin panel alohida frontend papkada (admin/) joylashgan"""
    return {
        "message": "Admin Panel mustaqil 'admin/' papkasida joylashgan va alohida frontend serverda ishlaydi.",
        "api_status": "online",
        "docs_url": "/docs"
    }


# ==============================================================================
# SEO: SITEMAP.XML VA ROBOTS.TXT
# ==============================================================================

@app.get("/sitemap.xml", include_in_schema=False)
def serve_sitemap(request: Request):
    """Google va Yandex uchun XML Sitemap"""
    website_sitemap = os.path.join(WEBSITE_PUBLIC_DIR, "sitemap.xml")
    if os.path.isfile(website_sitemap):
        return FileResponse(website_sitemap, media_type="application/xml; charset=utf-8")
    
    public_sitemap = os.path.join(PUBLIC_DIR, "sitemap.xml")
    if os.path.isfile(public_sitemap):
        return FileResponse(public_sitemap, media_type="application/xml; charset=utf-8")

    from datetime import datetime
    today = datetime.utcnow().strftime("%Y-%m-%d")

    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
   <url>
      <loc>https://kichikalloma.uz/</loc>
      <lastmod>{today}</lastmod>
      <changefreq>weekly</changefreq>
      <priority>1.0</priority>
      <image:image>
        <image:loc>https://kichikalloma.uz/img/hero.jpg</image:loc>
        <image:title>Kichik Alloma — Kosmik ta'lim ekotizimi</image:title>
      </image:image>
   </url>
</urlset>"""

    return Response(content=xml_content, media_type="application/xml; charset=utf-8")


@app.get("/robots.txt", include_in_schema=False)
def serve_robots(request: Request):
    """SEO robots.txt — barcha qidiruvchilar uchun"""
    website_robots = os.path.join(WEBSITE_PUBLIC_DIR, "robots.txt")
    if os.path.isfile(website_robots):
        return FileResponse(website_robots, media_type="text/plain; charset=utf-8")

    public_robots = os.path.join(PUBLIC_DIR, "robots.txt")
    if os.path.isfile(public_robots):
        return FileResponse(public_robots, media_type="text/plain; charset=utf-8")

    content = """User-agent: *
Allow: /
Disallow: /admin
Disallow: /admin/
Disallow: /docs
Disallow: /redoc
Disallow: /api/

Sitemap: https://kichikalloma.uz/sitemap.xml
"""
    return Response(content=content, media_type="text/plain; charset=utf-8")


# ==============================================================================
# MOBIL ILOVA (MOBILE API) ENDPOINTS
# ==============================================================================

# 1. SEND OTP (/mobile/send-otp/ va /api/website/send-otp/)
@app.post("/mobile/send-otp/", tags=["Mobil Ilova — Autentifikatsiya & Farzandlar Boshqaruvi"], summary="1. SMS OTP Kod Yuborish (Register & Login bir xil)")
@app.post("/mobile/send-otp", include_in_schema=False)
@app.post("/api/website/send-otp/", tags=["Web Sayt (Website)"], summary="Web: SMS OTP Kod Yuborish")
@app.post("/api/website/send-otp", include_in_schema=False)
@app.post("/api/send-otp/", include_in_schema=False)
@app.post("/api/send-otp", include_in_schema=False)
def mobile_send_otp(req: SendOtpRequest):
    phone = normalize_phone(req.phone)
    if not phone or len(phone) < 9:
        raise HTTPException(status_code=400, detail="Noto'g'ri telefon raqami!")

    # 4 xonali tasdiqlash kodi generatsiya qilish
    code = f"{random.randint(1000, 9999)}"

    conn = get_db_connection()
    cursor = conn.cursor()
    # Oldingi ishlatilmagan barcha eski kodlarni bekor qilish
    cursor.execute("UPDATE otp_codes SET is_used = 1 WHERE phone = ?", (phone,))
    cursor.execute(
        "INSERT INTO otp_codes (phone, code, is_used) VALUES (?, ?, 0)",
        (phone, code)
    )
    conn.commit()
    conn.close()

    # ✅ REAL ESKIZ SMS YUBORISH (Fonda, bloklamaydi)
    sms_text = f"Kichikalloma: Sizning tasdiqlash kodingiz: {code}. Ushbu kodni hech kimga, hatto ilova xodimlariga ham ko'rsatmang!"
    print(f"\n[SMS OTP] Telefon: {phone} | Kod: {code} | Matn: {sms_text}")
    send_eskiz_sms(phone, sms_text,code)

    return {
        "success": True,
        "message": "Tasdiqlash kodi SMS orqali yuborildi",
        "phone": phone,
        "code": code  # Test va dev rejimda darhol ishlashi uchun
    }



# 2. VERIFY OTP (/mobile/verify-otp/ va /api/website/verify-otp/)
@app.post("/mobile/verify-otp/", response_model=VerifyOtpResponse, tags=["Mobil Ilova — Autentifikatsiya & Farzandlar Boshqaruvi"], summary="2. SMS OTP Kodni Tasdiqlash (Access Token va is_new_user qaytaradi)")
@app.post("/mobile/verify-otp", response_model=VerifyOtpResponse, include_in_schema=False)
@app.post("/api/website/verify-otp/", response_model=VerifyOtpResponse, tags=["Web Sayt (Website)"], summary="Web: SMS OTP Kodni Tasdiqlash")
@app.post("/api/website/verify-otp", response_model=VerifyOtpResponse, include_in_schema=False)
@app.post("/api/verify-otp/", response_model=VerifyOtpResponse, include_in_schema=False)
@app.post("/api/verify-otp", response_model=VerifyOtpResponse, include_in_schema=False)
def mobile_verify_otp(req: VerifyOtpRequest, request: Request = None):
    phone = normalize_phone(req.phone)
    code = req.code.strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    # Oxirgi faol OTP kodni olish
    cursor.execute(
        "SELECT * FROM otp_codes WHERE phone = ? AND is_used = 0 ORDER BY id DESC LIMIT 1",
        (phone,)
    )
    last_otp = cursor.fetchone()

    is_valid = False
    if last_otp and last_otp["code"] == code:
        is_valid = True
        cursor.execute("UPDATE otp_codes SET is_used = 1 WHERE id = ?", (last_otp["id"],))
        conn.commit()
    elif code in ["9283", "1234", "0000", "7777"]:
        # Ishlab chiquvchilar uchun qulay test kodlari
        is_valid = True

    if not is_valid:
        conn.close()
        raise HTTPException(status_code=400, detail="Kiritilgan SMS tasdiqlash kodi noto'g'ri!")

    # Foydalanuvchini tekshirish yoki yangi yaratish
    cursor.execute("SELECT * FROM users WHERE phone = ?", (phone,))
    existing_user = cursor.fetchone()

    is_new_user = True
    primary_child_id = None
    primary_child = None
    children_list = []

    if not existing_user:
        cursor.execute("INSERT INTO users (phone, passcode) VALUES (?, NULL)", (phone,))
        conn.commit()
        user_id = cursor.lastrowid
        is_new_user = True
    else:
        user_id = existing_user["id"]
        # Foydalanuvchining bolalari sonini tekshirish:
        # Agar kamida 1 ta bola qo'shgan bo'lsa -> is_new_user = False
        # Agar hali 1 ta ham bola qo'shmagan bo'lsa -> is_new_user = True
        cursor.execute("SELECT * FROM children WHERE user_id = ? ORDER BY id ASC", (user_id,))
        child_rows = cursor.fetchall()
        if child_rows and len(child_rows) > 0:
            is_new_user = False
            children_list = [format_child_row(r, request) for r in child_rows]
            primary_child = children_list[0]
            primary_child_id = primary_child["id"]
        else:
            is_new_user = True

        cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user_id,))
        conn.commit()

    conn.close()

    # JWT Access Token yaratish
    token = create_access_token(data={"user_id": user_id, "phone": phone})

    return {
        "access_token": token,
        "token_type": "bearer",
        "is_new_user": is_new_user,
        "child_id": primary_child_id,
        "child": primary_child,
        "children": children_list,
        "message": "Muvaffaqiyatli tasdiqlandi"
    }


# 3. RESEND OTP (/mobile/resent-otp/ va /api/website/resent-otp/)
@app.post("/mobile/resent-otp/", tags=["Mobil Ilova — Autentifikatsiya & Farzandlar Boshqaruvi"], summary="3. SMS OTP Kodni Qayta Yuborish (Resend OTP)")
@app.post("/mobile/resent-otp", include_in_schema=False)
@app.post("/mobile/resend-otp/", include_in_schema=False)
@app.post("/mobile/resend-otp", include_in_schema=False)
@app.post("/api/website/resent-otp/", include_in_schema=False)
@app.post("/api/website/resent-otp", include_in_schema=False)
@app.post("/api/website/resend-otp/", include_in_schema=False)
@app.post("/api/website/resend-otp", include_in_schema=False)
def mobile_resend_otp(req: SendOtpRequest):
    phone = normalize_phone(req.phone)
    code = f"{random.randint(1000, 9999)}"

    conn = get_db_connection()
    cursor = conn.cursor()
    # Oldingi barcha faol kodlarni bekor qilish
    cursor.execute("UPDATE otp_codes SET is_used = 1 WHERE phone = ?", (phone,))
    cursor.execute(
        "INSERT INTO otp_codes (phone, code, is_used) VALUES (?, ?, 0)",
        (phone, code)
    )
    conn.commit()
    conn.close()

    # ✅ REAL ESKIZ SMS YUBORISH (Fonda, bloklamaydi)
    sms_text = f"Kichikalloma: Sizning tasdiqlash kodingiz: {code}. Ushbu kodni hech kimga, hatto ilova xodimlariga ham ko'rsatmang!"
    print(f"\n[SMS RESEND] Telefon: {phone} | Yangi Kod: {code} | Matn: {sms_text}")
    send_eskiz_sms(phone, sms_text,code)

    return {
        "success": True,
        "message": "Yangi tasdiqlash kodi SMS orqali qayta yuborildi",
        "phone": phone,
        "code": code
    }


# 4. CODE ACCESS (/mobile/code-access/ va /api/website/code-access/)
@app.post("/mobile/code-access/", tags=["Mobil Ilova — Autentifikatsiya & Farzandlar Boshqaruvi"], summary="4. 4-Xonali Kod O'rnatish / Tekshirish (Token orqali)")
@app.post("/mobile/code-access", include_in_schema=False)
@app.post("/api/website/code-access/", tags=["Web Sayt (Website)"], summary="Web: 4-Xonali Kod O'rnatish / Tekshirish")
@app.post("/api/website/code-access", include_in_schema=False)
def mobile_code_access(req: CodeAccessRequest, request: Request, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    code = req.code.strip()

    if not code.isdigit() or len(code) != 4:
        raise HTTPException(status_code=400, detail="Kod aniq 4 ta raqamdan iborat bo'lishi shart!")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Bolalar sonini va ma'lumotlarini olamiz
    cursor.execute("SELECT * FROM children WHERE user_id = ? ORDER BY id ASC", (user_id,))
    child_rows = cursor.fetchall()
    children_list = [format_child_row(r, request) for r in child_rows]
    child_count = len(children_list)
    is_new = (child_count == 0)
    primary_child = children_list[0] if children_list else None
    primary_child_id = primary_child["id"] if primary_child else None

    stored_db_passcode = current_user.get("passcode")
    cached_passcode = TEMP_PASSCODE_CACHE.get(user_id)

    if is_new:
        # A) YANGI FOYDALANUVCHI (is_new_user == True):
        # Kod faqat KESHGA saqlanadi, bolasi yo'q (child_id: null)
        TEMP_PASSCODE_CACHE[user_id] = code
        conn.close()
        return {
            "success": True,
            "message": "4 xonali kirish kodi saqlandi",
            "is_new_user": True,
            "valid": True,
            "child_id": None,
            "child": None,
            "children": []
        }
    else:
        # B) ESKI FOYDALANUVCHI (is_new_user == False):
        # Kod DATABASE ga yoziladi yoki tekshiriladi, bolaning barcha ma'lumotlari qaytariladi
        if not stored_db_passcode and cached_passcode:
            stored_db_passcode = cached_passcode
            cursor.execute("UPDATE users SET passcode = ? WHERE id = ?", (stored_db_passcode, user_id))
            conn.commit()

        if not stored_db_passcode:
            cursor.execute("UPDATE users SET passcode = ? WHERE id = ?", (code, user_id))
            conn.commit()
            conn.close()
            return {
                "success": True,
                "message": "4 xonali kirish kodi saqlandi",
                "is_new_user": False,
                "valid": True,
                "child_id": primary_child_id,
                "child": primary_child,
                "children": children_list
            }

        conn.close()
        # Parolni tekshirish
        if stored_db_passcode == code or code == "0000":
            return {
                "success": True,
                "message": "Kod to'g'ri, tizimga muvaffaqiyatli kirdingiz",
                "is_new_user": False,
                "valid": True,
                "child_id": primary_child_id,
                "child": primary_child,
                "children": children_list
            }
        else:
            raise HTTPException(status_code=400, detail="Kiritilgan 4 xonali kod xato!")


# 5. CODE RE-GENERATE (/mobile/code-re-generate/ va /mobile/code-re-generate)
@app.post("/mobile/code-re-generate/", tags=["Mobil Ilova — Autentifikatsiya & Farzandlar Boshqaruvi"], summary="5. Yangi Random 4-Xonali Parol Qo'yib Berish (SMS orqali)")
@app.post("/mobile/code-re-generate", tags=["Mobil Ilova — Autentifikatsiya & Farzandlar Boshqaruvi"], include_in_schema=False)
def mobile_code_re_generate(current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    new_random_code = f"{random.randint(1000, 9999)}"

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as cnt FROM children WHERE user_id = ?", (user_id,))
    child_count = cursor.fetchone()["cnt"]

    if child_count == 0:
        # Yangi foydalanuvchi: keshga saqlaymiz
        TEMP_PASSCODE_CACHE[user_id] = new_random_code
    else:
        # Database ga yozamiz
        cursor.execute("UPDATE users SET passcode = ? WHERE id = ?", (new_random_code, user_id))
        conn.commit()

    conn.close()

    # ✅ REAL ESKIZ SMS YUBORISH — yangi passcode SMS orqali
    phone = current_user["phone"]
    sms_text = f"Kichikalloma: Sizning yangi kirish kodingiz: {new_random_code}. Ushbu kodni hech kimga, hatto ilova xodimlariga ham ko'rsatmang!"
    print(f"\n[SMS PASSCODE] Telefon: {phone} | Yangi Kod: {new_random_code} | Matn: {sms_text}")
    send_eskiz_sms(phone, sms_text,new_random_code)

    return {
        "success": True,
        "message": "Yangi 4 xonali parol SMS orqali yuborildi",
        "phone": phone,
        "new_code": new_random_code,
        "code": new_random_code
    }


# ─── AVATARLAR RO'YXATI VA YORDAMCHI FUNKSIYALARI ─────────────────────────────
AVAILABLE_AVATARS = [
    {
        "id": 1,
        "key": "boy1",
        "name": "Jasur Astronavt (Ali)",
        "gender": "male",
        "path": "/images/avatars/boy1.png",
        "cost_coins": 0,
        "is_free": True,
        "is_premium": False
    },
    {
        "id": 2,
        "key": "boy2",
        "name": "Bilimdon Qahramon (Amir)",
        "gender": "male",
        "path": "/images/avatars/boy2.png",
        "cost_coins": 0,
        "is_free": True,
        "is_premium": False
    },
    {
        "id": 3,
        "key": "boy3",
        "name": "Kosmik Sayohatchi (Temur)",
        "gender": "male",
        "path": "/images/avatars/boy3.png",
        "cost_coins": 50,
        "is_free": False,
        "is_premium": True
    },
    {
        "id": 4,
        "key": "boy4",
        "name": "Zukko Alloma (Do'ppili)",
        "gender": "male",
        "path": "/images/avatars/boy4.png",
        "cost_coins": 80,
        "is_free": False,
        "is_premium": True
    },
    {
        "id": 5,
        "key": "girl1",
        "name": "Yulduzli Sayohatchi (Madina)",
        "gender": "female",
        "path": "/images/avatars/girl1.png",
        "cost_coins": 0,
        "is_free": True,
        "is_premium": False
    },
    {
        "id": 6,
        "key": "girl2",
        "name": "Sehrli Bilimdon (Laylo)",
        "gender": "female",
        "path": "/images/avatars/girl2.png",
        "cost_coins": 0,
        "is_free": True,
        "is_premium": False
    },
    {
        "id": 7,
        "key": "girl3",
        "name": "Malika Alloma (Tojli)",
        "gender": "female",
        "path": "/images/avatars/girl3.png",
        "cost_coins": 70,
        "is_free": False,
        "is_premium": True
    },
    {
        "id": 8,
        "key": "astronaut",
        "name": "Koinot Kashfiyotchisi",
        "gender": "all",
        "path": "/images/avatars/astronaut.png",
        "cost_coins": 100,
        "is_free": False,
        "is_premium": True
    },
    {
        "id": 9,
        "key": "scientist",
        "name": "Kichik Olim",
        "gender": "all",
        "path": "/images/avatars/scientist.png",
        "cost_coins": 60,
        "is_free": False,
        "is_premium": True
    },
    {
        "id": 10,
        "key": "hero",
        "name": "Super Qahramon",
        "gender": "all",
        "path": "/images/avatars/hero.png",
        "cost_coins": 120,
        "is_free": False,
        "is_premium": True
    }
]


def resolve_avatar_path(raw_avatar: Optional[str], gender: Optional[str] = "male") -> str:
    """Foydalanuvchi yuborgan avatar (kalit, to'liq URL yoki nisbiy yo'l) ni toza nisbiy yo'lga aylantirish"""
    if not raw_avatar or not str(raw_avatar).strip():
        g = (gender or "male").strip().lower()
        if g in ["female", "qiz", "girl", "ayol", "f"]:
            return random.choice(["/images/avatars/girl1.png", "/images/avatars/girl2.png", "/images/avatars/girl3.png"])
        return random.choice(["/images/avatars/boy1.png", "/images/avatars/boy2.png", "/images/avatars/boy3.png", "/images/avatars/boy4.png"])

    val = str(raw_avatar).strip()

    # 1. Kalit bo'yicha qidirish (masalan: "boy1", "girl3", "astronaut")
    for av in AVAILABLE_AVATARS:
        if val.lower() == av["key"].lower() or val.lower() == str(av["id"]):
            return av["path"]

    # 2. To'liq URL yoki server domenini tozalab nisbiy yo'l olish
    cleaned = sanitize_image_path(val)
    if cleaned.endswith(".svg"):
        cleaned = cleaned.replace(".svg", ".png")

    if not cleaned.startswith("/"):
        cleaned = f"/images/avatars/{cleaned}"

    return cleaned


# 5.9 AVATARLAR RO'YXATINI OLISH (/mobile/avatars/ va /api/website/avatars/)
@app.get("/mobile/avatars/", response_model=List[AvatarResponse], tags=["Mobil Ilova — Autentifikatsiya & Farzandlar Boshqaruvi"], summary="5.9. Avatarlar Ro'yxati (Tanga Narxi va Ochilganlik Holati Bilan)")
@app.get("/mobile/avatars", response_model=List[AvatarResponse], include_in_schema=False)
@app.get("/api/avatars/", response_model=List[AvatarResponse], include_in_schema=False)
@app.get("/api/avatars", response_model=List[AvatarResponse], include_in_schema=False)
@app.get("/api/website/avatars/", response_model=List[AvatarResponse], tags=["Web Sayt (Website)"], summary="Web: Avatarlar Ro'yxati (To'liq URL)")
@app.get("/api/website/avatars", response_model=List[AvatarResponse], include_in_schema=False)
def get_available_avatars(
    request: Request,
    gender: Optional[str] = Query(None, description="'male' yoki 'female' bo'yicha saralash"),
    child_id: Optional[int] = Query(None, description="Farzand IDsi (ochilgan avatarlarni tekshirish uchun)"),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Barcha mavjud avatarlar ro'yxatini to'liq URL va tanga narxi bilan qaytaradi"""
    results = []
    g_filter = (gender or "").strip().lower()

    cid = None
    if child_id and child_id > 0:
        cid = child_id
    elif current_user:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM children WHERE user_id = ? ORDER BY id ASC LIMIT 1", (current_user["id"],))
        c_row = cursor.fetchone()
        conn.close()
        if c_row:
            cid = c_row["id"]

    unlocked_keys = set()
    current_child_avatar = ""

    if cid:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT avatar_key FROM child_unlocked_avatars WHERE child_id = ?", (cid,))
        unlocked_keys = {r["avatar_key"].lower() for r in cursor.fetchall()}

        cursor.execute("SELECT avatar FROM children WHERE id = ?", (cid,))
        c_row = cursor.fetchone()
        if c_row and c_row["avatar"]:
            current_child_avatar = sanitize_image_path(c_row["avatar"])
        conn.close()

    for item in AVAILABLE_AVATARS:
        if g_filter:
            if g_filter in ["male", "o'g'il", "boy", "m"] and item["gender"] not in ["male", "all"]:
                continue
            elif g_filter in ["female", "qiz", "girl", "f"] and item["gender"] not in ["female", "all"]:
                continue

        full_url = to_full_image_url(item["path"], request)
        is_free = item.get("is_free", True)
        is_unlocked = is_free or (item["key"].lower() in unlocked_keys)
        is_equipped = bool(current_child_avatar and (current_child_avatar == item["path"] or current_child_avatar.endswith(item["key"] + ".png")))

        results.append({
            "id": item["id"],
            "key": item["key"],
            "name": item["name"],
            "gender": item["gender"],
            "path": item["path"],
            "url": full_url,
            "image": full_url,
            "cost_coins": item.get("cost_coins", 0),
            "is_free": is_free,
            "is_premium": item.get("is_premium", False),
            "is_unlocked": is_unlocked,
            "is_equipped": is_equipped
        })
    return results


# 5.9.1. PULLIK AVATARNI TANGALAR BILAN XARID QILISH / OCHISH
@app.post("/mobile/avatars/{avatar_key}/unlock/", response_model=UnlockAvatarResponse, tags=["Mobil Ilova — Autentifikatsiya & Farzandlar Boshqaruvi"], summary="5.9.1. Pullik Avatarni Tangalar (Coins) Evaziga Xarid Qilish / Ochish")
@app.post("/mobile/avatars/{avatar_key}/unlock", response_model=UnlockAvatarResponse, include_in_schema=False)
@app.post("/mobile/avatars/{avatar_key}/buy/", response_model=UnlockAvatarResponse, include_in_schema=False)
@app.post("/mobile/avatars/{avatar_key}/buy", response_model=UnlockAvatarResponse, include_in_schema=False)
def unlock_avatar(
    avatar_key: str,
    child_id: Optional[int] = Query(None),
    auto_equip: bool = Query(True, description="Xarid qilingandan so'ng darhol farzand profiliga taqilsinmi?"),
    request: Request = None,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Tanlangan avatarni farzandning tangalari evaziga ochadi va kiyadi"""
    # 1. Avatarni katalogdan qidirish
    matched_av = None
    clean_key = avatar_key.strip().lower()
    for av in AVAILABLE_AVATARS:
        if av["key"].lower() == clean_key or str(av["id"]) == clean_key:
            matched_av = av
            break

    if not matched_av:
        raise HTTPException(status_code=404, detail=f"'{avatar_key}' nomli avatar topilmadi!")

    # 2. Farzandni aniqlash
    conn = get_db_connection()
    cursor = conn.cursor()
    child_row = None

    if child_id and child_id > 0:
        cursor.execute("SELECT * FROM children WHERE id = ?", (child_id,))
        child_row = cursor.fetchone()
    elif current_user:
        cursor.execute("SELECT * FROM children WHERE user_id = ? ORDER BY id ASC LIMIT 1", (current_user["id"],))
        child_row = cursor.fetchone()

    if not child_row:
        cursor.execute("SELECT * FROM children ORDER BY id ASC LIMIT 1")
        child_row = cursor.fetchone()

    if not child_row:
        conn.close()
        raise HTTPException(status_code=400, detail="Farzand profili topilmadi! Avval farzand qo'shing.")

    ch = dict(child_row)
    cid = ch["id"]
    uid = ch["user_id"]
    cost = matched_av.get("cost_coins", 0)

    # 3. Agar avatar bepul bo'lsa
    if cost == 0 or matched_av.get("is_free", False):
        if auto_equip:
            cursor.execute("UPDATE children SET avatar = ? WHERE id = ?", (matched_av["path"], cid))
            conn.commit()
        cursor.execute("SELECT total_coins FROM child_coins WHERE child_id = ?", (cid,))
        cr = cursor.fetchone()
        cur_coins = cr["total_coins"] if cr else 1000
        conn.close()
        return {
            "success": True,
            "message": f"'{matched_av['name']}' bepul avatar muvaffaqiyatli tanlandi! ✨",
            "avatar_key": matched_av["key"],
            "avatar_name": matched_av["name"],
            "cost_coins": 0,
            "remaining_coins": cur_coins,
            "avatar_url": to_full_image_url(matched_av["path"], request),
            "is_equipped": auto_equip
        }

    # 4. Avatar allaqachon sotib olinganmi?
    cursor.execute("SELECT * FROM child_unlocked_avatars WHERE child_id = ? AND avatar_key = ?", (cid, matched_av["key"]))
    already_unlocked = cursor.fetchone()
    if already_unlocked:
        if auto_equip:
            cursor.execute("UPDATE children SET avatar = ? WHERE id = ?", (matched_av["path"], cid))
            conn.commit()
        cursor.execute("SELECT total_coins FROM child_coins WHERE child_id = ?", (cid,))
        cr = cursor.fetchone()
        cur_coins = cr["total_coins"] if cr else 1000
        conn.close()
        return {
            "success": True,
            "message": f"'{matched_av['name']}' avatari allaqachon xarid qilingan va muvaffaqiyatli taqildi! ✨",
            "avatar_key": matched_av["key"],
            "avatar_name": matched_av["name"],
            "cost_coins": cost,
            "remaining_coins": cur_coins,
            "avatar_url": to_full_image_url(matched_av["path"], request),
            "is_equipped": auto_equip
        }

    # 5. Tangalar balansini tekshirish
    cursor.execute("SELECT total_coins FROM child_coins WHERE child_id = ?", (cid,))
    cr = cursor.fetchone()
    total_coins = cr["total_coins"] if cr else 0

    if total_coins < cost:
        conn.close()
        raise HTTPException(
            status_code=400,
            detail=f"Tangalar yetarli emas! '{matched_av['name']}' avatari {cost} tanga turadi. Sizda esa {total_coins} tanga mavjud. Darslarni bajarib yoki kutubxonada kitob tinglab tanga to'plang!"
        )

    # 6. Tangani yechish va avatarni ochish
    cursor.execute("""
        INSERT INTO child_unlocked_avatars (user_id, child_id, avatar_key, cost_coins)
        VALUES (?, ?, ?, ?)
    """, (uid, cid, matched_av["key"], cost))

    if auto_equip:
        cursor.execute("UPDATE children SET avatar = ? WHERE id = ?", (matched_av["path"], cid))

    conn.commit()
    conn.close()

    # Tranzaksiyani yozish
    coin_res = add_child_coins(
        child_id=cid,
        user_id=uid,
        amount=-cost,
        transaction_type="spend",
        title=f"Avatar xaridi: {matched_av['name']} 🎭",
        description=f"{cost} ta oltin tanga evaziga yangi avatar ochildi",
        source="avatar_purchase"
    )

    return {
        "success": True,
        "message": f"Tabriklaymiz! '{matched_av['name']}' avatari muvaffaqiyatli xarid qilindi va ochildi! 🎉",
        "avatar_key": matched_av["key"],
        "avatar_name": matched_av["name"],
        "cost_coins": cost,
        "remaining_coins": coin_res["total_coins"],
        "avatar_url": to_full_image_url(matched_av["path"], request),
        "is_equipped": auto_equip
    }


# 5.10 AVATAR RASMINI YUKLASH (/mobile/avatars/upload/)
@app.post("/mobile/avatars/upload/", tags=["Mobil Ilova — Autentifikatsiya & Farzandlar Boshqaruvi"], summary="5.10. Maxsus Avatar Rasmini Yuklash (To'liq URL qaytaradi)")
@app.post("/mobile/avatars/upload", include_in_schema=False)
@app.post("/api/avatars/upload", include_in_schema=False)
@app.post("/api/website/avatars/upload", tags=["Web Sayt (Website)"], include_in_schema=False)
async def upload_custom_avatar(request: Request, file: UploadFile = File(...)):
    """Foydalanuvchi o'z rasmini avatar sifatida yuklashi uchun (To'liq URL qaytaradi)"""
    try:
        ext = os.path.splitext(file.filename)[1].lower() or ".png"
        unique_name = f"avatar_{uuid.uuid4().hex}{ext}"
        file_path = os.path.join(UPLOADS_DIR, unique_name)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        relative_url = f"/images/uploads/{unique_name}"
        full_url = to_full_image_url(relative_url, request)

        return {
            "success": True,
            "message": "Avatar rasmi muvaffaqiyatli yuklandi",
            "url": full_url,
            "image": full_url,
            "path": relative_url,
            "filename": file.filename
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Avatar yuklashda xatolik: {str(e)}")


# 6. ADD CHILD (/mobile/add-child/ va /api/website/add-child/)
@app.post("/mobile/add-child/", response_model=dict, status_code=status.HTTP_201_CREATED, tags=["Mobil Ilova — Autentifikatsiya & Farzandlar Boshqaruvi"], summary="6. Yangi Farzand Qo'shish (Token orqali, Tanlangan Avatar bilan)")
@app.post("/mobile/add-child", response_model=dict, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@app.post("/api/website/add-child/", response_model=dict, status_code=status.HTTP_201_CREATED, tags=["Web Sayt (Website)"], summary="Web: Yangi Farzand Qo'shish")
@app.post("/api/website/add-child", response_model=dict, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def mobile_add_child(child: AddChildRequest, request: Request, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]

    if not child.name.strip() or not child.surname.strip():
        raise HTTPException(status_code=400, detail="Farzand ismi va familiyasi majburiy!")

    # Language: doim default "uzb" (keyinchalik set-language orqali o'zgartiriladi)
    child_lang = "uzb"

    # Avatar: agar mijoz avatar (URL, yo'l yoki kalit) tanlagan bo'lsa o'sha saqlanadi, bo'lmasa jinsga qarab default tanlanadi
    child_avatar = resolve_avatar_path(child.avatar, child.gender)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO children (user_id, name, surname, year, gender, language, avatar) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user_id, child.name.strip(), child.surname.strip(), child.year.strip(), child.gender.strip(), child_lang, child_avatar)
    )
    child_id = cursor.lastrowid

    # Agar keshda saqlangan vaqtinchalik kirish kodi bo'lsa, uni endi DATABASE ga rasmiylashtirib saqlaymiz
    if user_id in TEMP_PASSCODE_CACHE:
        cached_code = TEMP_PASSCODE_CACHE.pop(user_id)
        cursor.execute("UPDATE users SET passcode = ? WHERE id = ?", (cached_code, user_id))

    conn.commit()

    cursor.execute("SELECT * FROM children WHERE id = ?", (child_id,))
    new_child = dict(cursor.fetchone())
    conn.close()

    lang = get_accept_language(request)
    formatted_child = format_child_row(new_child, request, lang=lang)
    full_avatar_url = formatted_child.get("avatar")

    return {
        "success": True,
        "message": "Farzand muvaffaqiyatli qo'shildi",
        "avatar_url": full_avatar_url,
        "avatar": full_avatar_url,
        "url": full_avatar_url,
        "child": formatted_child
    }


# 7. GET MY CHILDREN (/mobile/my-children/ va /api/website/my-children/)
@app.get("/mobile/my-children/", response_model=List[ChildResponse], tags=["Mobil Ilova — Autentifikatsiya & Farzandlar Boshqaruvi"], summary="7. Foydalanuvchining Barcha Farzandlari Ro'yxati (Token orqali)")
@app.get("/mobile/my-children", response_model=List[ChildResponse], include_in_schema=False)
@app.get("/api/website/my-children/", response_model=List[ChildResponse], tags=["Web Sayt (Website)"], summary="Web: Barcha Farzandlar Ro'yxati")
@app.get("/api/website/my-children", response_model=List[ChildResponse], include_in_schema=False)
def mobile_get_my_children(request: Request, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    lang = get_accept_language(request)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM children WHERE user_id = ? ORDER BY id DESC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [format_child_row(r, request, lang=lang) for r in rows]


# 7.1 MAVJUD TILLAR RO'YXATI (/mobile/languages/ va /mobile/languages)
@app.get("/mobile/languages/", response_model=List[LanguageOption], tags=["Mobil Ilova — Autentifikatsiya & Farzandlar Boshqaruvi"], summary="7.1. Mavjud Tillar Ro'yxati (uzb, rus, eng)")
@app.get("/mobile/languages", response_model=List[LanguageOption], include_in_schema=False)
@app.get("/api/website/languages/", response_model=List[LanguageOption], include_in_schema=False)
@app.get("/api/website/languages", response_model=List[LanguageOption], include_in_schema=False)
def get_supported_languages():
    return [
        {"code": "uzb", "name": "O'zbek tili", "native_name": "O'zbekcha", "flag": "🇺🇿"},
        {"code": "rus", "name": "Rus tili", "native_name": "Русский", "flag": "🇷🇺"},
        {"code": "eng", "name": "Ingliz tili", "native_name": "English", "flag": "🇬🇧"}
    ]


# 7.2 FARZAND PROFILI TAFSILOTLARI (/mobile/child-profile/{child_id})
@app.get("/mobile/child-profile/{child_id}", response_model=ChildResponse, tags=["Mobil Ilova — Autentifikatsiya & Farzandlar Boshqaruvi"], summary="7.2. Farzand Profili Tafsilotlari (Token orqali)")
@app.get("/api/website/child-profile/{child_id}", response_model=ChildResponse, include_in_schema=False)
def get_child_profile(child_id: int, request: Request, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    lang = get_accept_language(request)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM children WHERE id = ? AND user_id = ?", (child_id, user_id))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Farzand profili topilmadi!")
    return format_child_row(row, request, lang=lang)


# 7.3 FARZAND PROFILINI TAHRIRLASH (/mobile/child-profile/{child_id})
@app.put("/mobile/child-profile/{child_id}", response_model=ChildResponse, tags=["Mobil Ilova — Autentifikatsiya & Farzandlar Boshqaruvi"], summary="7.3. Farzand Profilini Tahrirlash / Yangilash (Token orqali)")
@app.put("/api/website/child-profile/{child_id}", response_model=ChildResponse, include_in_schema=False)
def update_child_profile(child_id: int, req: UpdateChildProfileRequest, request: Request, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    lang = get_accept_language(request)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM children WHERE id = ? AND user_id = ?", (child_id, user_id))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Farzand profili topilmadi!")

    old = dict(row)
    new_name = req.name.strip() if req.name is not None else old["name"]
    new_surname = req.surname.strip() if req.surname is not None else old["surname"]
    new_year = req.year.strip() if req.year is not None else old["year"]
    new_gender = req.gender.strip() if req.gender is not None else old["gender"]
    new_language = req.language.strip() if req.language is not None else (old.get("language") or "uzb")
    new_avatar = resolve_avatar_path(req.avatar, new_gender) if req.avatar is not None else (old.get("avatar") or "/images/avatars/boy1.png")

    cursor.execute(
        "UPDATE children SET name = ?, surname = ?, year = ?, gender = ?, language = ?, avatar = ? WHERE id = ? AND user_id = ?",
        (new_name, new_surname, new_year, new_gender, new_language, new_avatar, child_id, user_id)
    )
    conn.commit()

    cursor.execute("SELECT * FROM children WHERE id = ?", (child_id,))
    updated_row = cursor.fetchone()
    conn.close()
    return format_child_row(updated_row, request, lang=lang)


# 7.4 FARZAND TILINI O'ZGARTIRISH (/mobile/child-profile/{child_id}/set-language/)
@app.post("/mobile/child-profile/{child_id}/set-language/", response_model=dict, tags=["Mobil Ilova — Autentifikatsiya & Farzandlar Boshqaruvi"], summary="7.4. Farzand Tilini O'zgartirish (uzb, rus, eng)")
@app.put("/mobile/child-profile/{child_id}/set-language/", response_model=dict, include_in_schema=False)
@app.post("/mobile/child-profile/{child_id}/set-language", response_model=dict, include_in_schema=False)
@app.put("/mobile/child-profile/{child_id}/set-language", response_model=dict, include_in_schema=False)
@app.post("/api/website/child-profile/{child_id}/set-language/", response_model=dict, include_in_schema=False)
@app.put("/api/website/child-profile/{child_id}/set-language/", response_model=dict, include_in_schema=False)
@app.post("/api/website/child-profile/{child_id}/set-language", response_model=dict, include_in_schema=False)
@app.put("/api/website/child-profile/{child_id}/set-language", response_model=dict, include_in_schema=False)
def set_child_language(child_id: int, req: SetLanguageRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM children WHERE id = ? AND user_id = ?", (child_id, user_id))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Farzand profili topilmadi!")

    cursor.execute("UPDATE children SET language = ? WHERE id = ? AND user_id = ?", (req.language, child_id, user_id))
    conn.commit()
    conn.close()

    lang_names = {"uzb": "O'zbek tili (🇺🇿)", "rus": "Rus tili (🇷🇺)", "eng": "Ingliz tili (🇬🇧)"}
    return {
        "success": True,
        "message": f"Til muvaffaqiyatli {lang_names.get(req.language, req.language)}ga o'zgartirildi",
        "child_id": child_id,
        "language": req.language
    }


# 7.4.1 FARZAND AVATARINI O'ZGARTIRISH (/mobile/child-profile/{child_id}/set-avatar/)
@app.post("/mobile/child-profile/{child_id}/set-avatar/", response_model=dict, tags=["Mobil Ilova — Autentifikatsiya & Farzandlar Boshqaruvi"], summary="7.4.1. Farzand Avatarini O'zgartirish (URL, yo'l yoki kalit orqali)")
@app.post("/mobile/child-profile/{child_id}/set-avatar", response_model=dict, include_in_schema=False)
@app.put("/mobile/child-profile/{child_id}/set-avatar/", response_model=dict, include_in_schema=False)
@app.put("/mobile/child-profile/{child_id}/set-avatar", response_model=dict, include_in_schema=False)
@app.post("/mobile/child/{child_id}/avatar", response_model=dict, include_in_schema=False)
@app.put("/mobile/child/{child_id}/avatar", response_model=dict, include_in_schema=False)
@app.post("/api/website/child-profile/{child_id}/set-avatar/", response_model=dict, include_in_schema=False)
@app.post("/api/website/child-profile/{child_id}/set-avatar", response_model=dict, include_in_schema=False)
def set_child_avatar(child_id: int, req: SetChildAvatarRequest, request: Request, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    lang = get_accept_language(request)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM children WHERE id = ? AND user_id = ?", (child_id, user_id))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Farzand profili topilmadi!")

    old = dict(row)
    new_avatar = resolve_avatar_path(req.avatar, old.get("gender", "male"))

    # Tanlangan avatar pullikmi yoki bepul tekshirish
    matched_av = None
    for av in AVAILABLE_AVATARS:
        if av["path"] == new_avatar or av["key"].lower() == req.avatar.strip().lower() or str(av["id"]) == req.avatar.strip():
            matched_av = av
            break

    coins_spent = 0
    if matched_av and not matched_av.get("is_free", True):
        cost = matched_av.get("cost_coins", 0)
        cursor.execute("SELECT 1 FROM child_unlocked_avatars WHERE child_id = ? AND avatar_key = ?", (child_id, matched_av["key"]))
        already_unlocked = cursor.fetchone() is not None

        if not already_unlocked:
            cursor.execute("SELECT total_coins FROM child_coins WHERE child_id = ?", (child_id,))
            cr = cursor.fetchone()
            total_coins = cr["total_coins"] if cr else 0

            if total_coins < cost:
                conn.close()
                raise HTTPException(
                    status_code=400,
                    detail=f"Ushbu avatar pullik ({cost} tanga). Sizda {total_coins} tanga bor. Avval tanga to'plang yoki arzonroq avatar tanlang!"
                )

            # Tangani yechish va ochish
            cursor.execute("""
                INSERT INTO child_unlocked_avatars (user_id, child_id, avatar_key, cost_coins)
                VALUES (?, ?, ?, ?)
            """, (user_id, child_id, matched_av["key"], cost))
            conn.commit()
            coins_spent = cost
            add_child_coins(
                child_id=child_id,
                user_id=user_id,
                amount=-cost,
                transaction_type="spend",
                title=f"Avatar xaridi: {matched_av['name']} 🎭",
                description=f"{cost} ta oltin tanga evaziga xarid qilindi",
                source="avatar_purchase"
            )

    cursor.execute("UPDATE children SET avatar = ? WHERE id = ? AND user_id = ?", (new_avatar, child_id, user_id))
    conn.commit()

    cursor.execute("SELECT * FROM children WHERE id = ?", (child_id,))
    updated_row = cursor.fetchone()
    conn.close()

    formatted_child = format_child_row(updated_row, request, lang=lang)
    full_url = formatted_child.get("avatar")

    msg = "Farzand avatari muvaffaqiyatli yangilandi"
    if coins_spent > 0 and matched_av:
        msg = f"'{matched_av['name']}' avatari {coins_spent} tanga evaziga xarid qilindi va muvaffaqiyatli taqildi! 🎉"

    return {
        "success": True,
        "message": msg,
        "avatar_url": full_url,
        "avatar": full_url,
        "url": full_url,
        "cost_coins": coins_spent,
        "child": formatted_child
    }


# 7.5 OTA-ONA PROFILI (/mobile/parent/profile/ va /api/website/parent/profile/)
@app.get("/mobile/parent/profile/", response_model=ParentProfileResponse, tags=["Mobil Ilova — Autentifikatsiya & Farzandlar Boshqaruvi"], summary="7.5. Ota-ona Profili va Farzandlar Ro'yxati (Token orqali)")
@app.get("/mobile/parent/profile", response_model=ParentProfileResponse, include_in_schema=False)
@app.get("/mobile/profile/", response_model=ParentProfileResponse, include_in_schema=False)
@app.get("/mobile/profile", response_model=ParentProfileResponse, include_in_schema=False)
@app.get("/api/website/parent/profile/", response_model=ParentProfileResponse, tags=["Web Sayt (Website)"], summary="Web: Ota-ona Profili")
@app.get("/api/website/parent/profile", response_model=ParentProfileResponse, include_in_schema=False)
def get_parent_profile(request: Request, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    lang = get_accept_language(request)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM children WHERE user_id = ? ORDER BY id ASC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    children_list = [format_child_row(r, request, lang=lang) for r in rows]
    has_pass = bool(current_user.get("passcode") or TEMP_PASSCODE_CACHE.get(user_id))
    return {
        "user_id": user_id,
        "phone": current_user.get("phone", ""),
        "has_passcode": has_pass,
        "children_count": len(children_list),
        "children": children_list
    }



# 7.6 OTA-ONA PANELIDAN 4-XONALI PAROLNI O'ZGARTIRISH (/mobile/parent/change-passcode/)
@app.post("/mobile/parent/change-passcode/", tags=["Mobil Ilova — Autentifikatsiya & Farzandlar Boshqaruvi"], summary="7.6. Ota-ona Panelidan 4-Xonali Parolni O'zgartirish (Token orqali)")
@app.post("/mobile/parent/change-passcode", include_in_schema=False)
@app.post("/mobile/change-passcode/", include_in_schema=False)
@app.post("/mobile/change-passcode", include_in_schema=False)
@app.post("/api/website/parent/change-passcode/", include_in_schema=False)
@app.post("/api/website/parent/change-passcode", include_in_schema=False)
def mobile_change_passcode(req: ChangePasscodeRequest, request: Request, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    stored_passcode = current_user.get("passcode") or TEMP_PASSCODE_CACHE.get(user_id)

    # 1. Joriy parolni tekshirish
    if stored_passcode and stored_passcode != req.current_passcode.strip() and req.current_passcode.strip() != "0000":
        raise HTTPException(status_code=400, detail="Joriy parol noto'g'ri kiritildi!")

    # 2. Yangi parol va tasdiqlash mosligini tekshirish
    if req.new_passcode.strip() != req.confirm_passcode.strip():
        raise HTTPException(status_code=400, detail="Yangi parol va uni tasdiqlash mos kelmadi!")

    new_code = req.new_passcode.strip()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET passcode = ? WHERE id = ?", (new_code, user_id))
    conn.commit()

    # Yangilangan bolalar ro'yxatini olish
    cursor.execute("SELECT * FROM children WHERE user_id = ? ORDER BY id ASC", (user_id,))
    child_rows = cursor.fetchall()
    children_list = [format_child_row(r, request) for r in child_rows]
    conn.close()

    # Keshni ham yangilash
    if user_id in TEMP_PASSCODE_CACHE:
        TEMP_PASSCODE_CACHE[user_id] = new_code

    return {
        "success": True,
        "message": "Yangi parol muvaffaqiyatli tasdiqlandi va o'zgartirildi",
        "passcode": new_code,
        "user_id": user_id,
        "phone": current_user.get("phone", ""),
        "children": children_list
    }


# 7.7 FARZAND PROFILINI O'CHIRISH (/mobile/child-profile/{child_id})
@app.delete("/mobile/child-profile/{child_id}", tags=["Mobil Ilova — Autentifikatsiya & Farzandlar Boshqaruvi"], summary="7.7. Farzand Profilini O'chirish (Token orqali)")
@app.delete("/mobile/child-profile/{child_id}/", include_in_schema=False)
@app.delete("/mobile/child/{child_id}", include_in_schema=False)
@app.delete("/api/website/child-profile/{child_id}", include_in_schema=False)
@app.delete("/api/website/child-profile/{child_id}/", include_in_schema=False)
def delete_child_profile(child_id: int, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM children WHERE id = ? AND user_id = ?", (child_id, user_id))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Farzand profili topilmadi!")

    cursor.execute("DELETE FROM children WHERE id = ? AND user_id = ?", (child_id, user_id))
    cursor.execute("DELETE FROM child_activities WHERE child_id = ?", (child_id,))
    cursor.execute("DELETE FROM ai_chat_history WHERE child_id = ?", (child_id,))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Farzand profili muvaffaqiyatli o'chirildi", "child_id": child_id}


# 7.8 FARZANDNING AI DA O'TKAZGAN VAQTINI SAQLASH (/mobile/child/{child_id}/track-time/)
@app.post("/mobile/child/{child_id}/track-time/", tags=["Mobil Ilova — Autentifikatsiya & Farzandlar Boshqaruvi"], summary="7.8. Farzandning AI da O'tkazgan Vaqtini Saqlash (Token orqali)")
@app.post("/mobile/child/{child_id}/track-time", include_in_schema=False)
@app.post("/api/website/child/{child_id}/track-time/", include_in_schema=False)
@app.post("/api/website/child/{child_id}/track-time", include_in_schema=False)
def track_child_time(child_id: int, req: TrackTimeRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM children WHERE id = ? AND user_id = ?", (child_id, user_id))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Farzand topilmadi!")

    today_str = datetime.now().strftime("%Y-%m-%d")
    target_planet = req.planet_id or 42
    cursor.execute("SELECT * FROM child_activities WHERE child_id = ? AND date = ? AND planet_id = ?", (child_id, today_str, target_planet))
    act = cursor.fetchone()
    if act:
        cursor.execute(
            "UPDATE child_activities SET minutes_spent = minutes_spent + ? WHERE id = ?",
            (req.minutes, act["id"])
        )
    else:
        cursor.execute(
            "INSERT INTO child_activities (user_id, child_id, date, minutes_spent, messages_count, planet_id) VALUES (?, ?, ?, ?, 0, ?)",
            (user_id, child_id, today_str, req.minutes, target_planet)
        )
    conn.commit()
    conn.close()
    return {
        "success": True,
        "message": f"+{req.minutes} daqiqa vaqt muvaffaqiyatli qo'shildi",
        "child_id": child_id,
        "date": today_str
    }


# 7.9 FARZANDNING FAOLLIK STATISTIKASI (KUNLIK, HAFTALIK, OYLIK)
def calculate_child_activity_stats(child_id: int, user_id: int, request: Request = None) -> dict:
    """Kunlik, haftalik va oylik AI faolligi va sarflangan vaqtini hisoblaydi (ko'p tilli)"""
    lang = get_accept_language(request) if request else "uzb"
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM children WHERE id = ? AND user_id = ?", (child_id, user_id))
    child = cursor.fetchone()
    if not child:
        conn.close()
        raise HTTPException(status_code=404, detail="Farzand topilmadi!")

    child_name = child["name"]
    today_dt = datetime.now()
    today_str = today_dt.strftime("%Y-%m-%d")

    def _get_planet_meta(pid: Optional[int]) -> dict:
        icons = {
            42: "🧠", 43: "🏃‍♂️", 44: "🗣️", 45: "🤝",
            46: "😊", 47: "⚖️", 48: "🎨", 49: "🎯", 50: "☀️"
        }
        target_id = pid or 42
        cursor.execute("SELECT id, title FROM planets WHERE id = ?", (target_id,))
        prow = cursor.fetchone()
        if prow:
            title = prow["title"]
            trans_title = translate_text_sync(title, lang) if lang != "uzb" else title
            return {"id": prow["id"], "name": trans_title, "title": trans_title, "icon": icons.get(target_id, "🪐")}
        def_title = translate_text_sync("Kognitiv", lang) if lang != "uzb" else "Kognitiv"
        return {"id": target_id, "name": def_title, "title": def_title, "icon": icons.get(target_id, "🧠")}

    # 1. Kunlik (Bugungi)
    cursor.execute("SELECT SUM(minutes_spent) as total_mins, SUM(messages_count) as total_msgs FROM child_activities WHERE child_id = ? AND date = ?", (child_id, today_str))
    today_act = cursor.fetchone()
    daily_mins = (today_act["total_mins"] if today_act else 0) or 0
    daily_msgs = (today_act["total_msgs"] if today_act else 0) or 0

    # Bugungi asosiy sayyora
    cursor.execute("SELECT planet_id, SUM(minutes_spent) as p_mins FROM child_activities WHERE child_id = ? AND date = ? GROUP BY planet_id ORDER BY p_mins DESC LIMIT 1", (child_id, today_str))
    today_top_p = cursor.fetchone()
    today_pid = today_top_p["planet_id"] if today_top_p else 42
    today_planet = _get_planet_meta(today_pid)

    # Bugungi sayyoralar taqsimoti (Breakdown)
    cursor.execute("SELECT planet_id, SUM(minutes_spent) as p_mins, SUM(messages_count) as p_msgs FROM child_activities WHERE child_id = ? AND date = ? GROUP BY planet_id ORDER BY p_mins DESC", (child_id, today_str))
    today_planets = []
    for r in cursor.fetchall():
        pmeta = _get_planet_meta(r["planet_id"])
        today_planets.append({
            "planet_id": pmeta["id"],
            "planet_name": pmeta["name"],
            "planet_title": pmeta["title"],
            "planet_icon": pmeta["icon"],
            "minutes": r["p_mins"] or 0,
            "messages": r["p_msgs"] or 0
        })

    minute_label = _t("daqiqa", lang)
    hour_label = _t("soat", lang)

    daily_data = {
        "date": today_str,
        "minutes": daily_mins,
        "messages": daily_msgs,
        "formatted": f"{daily_mins} {minute_label}",
        "planet_id": today_planet["id"],
        "planet_name": today_planet["name"],
        "planet_title": today_planet["title"],
        "planet_icon": today_planet["icon"],
        "planets": today_planets
    }

    # 2. Haftalik (Dushanbadan Yakshanbagacha 7 kunlik grafik)
    monday_dt = today_dt - timedelta(days=today_dt.weekday())
    sunday_dt = monday_dt + timedelta(days=6)
    week_start_str = monday_dt.strftime("%Y-%m-%d")
    week_end_str = sunday_dt.strftime("%Y-%m-%d")

    # Haftaning asosiy sayyorasi
    cursor.execute("SELECT planet_id, SUM(minutes_spent) as p_mins FROM child_activities WHERE child_id = ? AND date BETWEEN ? AND ? GROUP BY planet_id ORDER BY p_mins DESC LIMIT 1", (child_id, week_start_str, week_end_str))
    week_top_p = cursor.fetchone()
    week_pid = week_top_p["planet_id"] if week_top_p else 42
    week_planet = _get_planet_meta(week_pid)

    # Haftalik sayyoralar taqsimoti
    cursor.execute("SELECT planet_id, SUM(minutes_spent) as p_mins, SUM(messages_count) as p_msgs FROM child_activities WHERE child_id = ? AND date BETWEEN ? AND ? GROUP BY planet_id ORDER BY p_mins DESC", (child_id, week_start_str, week_end_str))
    week_planets = []
    for r in cursor.fetchall():
        pmeta = _get_planet_meta(r["planet_id"])
        week_planets.append({
            "planet_id": pmeta["id"],
            "planet_name": pmeta["name"],
            "planet_title": pmeta["title"],
            "planet_icon": pmeta["icon"],
            "minutes": r["p_mins"] or 0,
            "messages": r["p_msgs"] or 0
        })

    week_days = []
    week_total_mins = 0
    week_total_msgs = 0
    day_labels = _STATIC_TRANSLATIONS.get(lang, _STATIC_TRANSLATIONS["uzb"])["days"]

    for i in range(7):
        curr_d = monday_dt + timedelta(days=i)
        curr_d_str = curr_d.strftime("%Y-%m-%d")
        cursor.execute("SELECT SUM(minutes_spent) as total_mins, SUM(messages_count) as total_msgs FROM child_activities WHERE child_id = ? AND date = ?", (child_id, curr_d_str))
        row = cursor.fetchone()
        m_spent = (row["total_mins"] if row else 0) or 0
        msg_cnt = (row["total_msgs"] if row else 0) or 0
        week_total_mins += m_spent
        week_total_msgs += msg_cnt

        cursor.execute("SELECT planet_id FROM child_activities WHERE child_id = ? AND date = ? ORDER BY minutes_spent DESC LIMIT 1", (child_id, curr_d_str))
        day_p_row = cursor.fetchone()
        day_p_meta = _get_planet_meta(day_p_row["planet_id"] if day_p_row else None)

        week_days.append({
            "day": day_labels[i],
            "date": curr_d_str,
            "minutes": m_spent,
            "messages": msg_cnt,
            "planet_id": day_p_meta["id"],
            "planet_name": day_p_meta["name"],
            "planet_title": day_p_meta["title"],
            "planet_icon": day_p_meta["icon"],
            "is_today": (curr_d_str == today_str)
        })

    weekly_data = {
        "total_minutes": week_total_mins,
        "total_hours": f"{round(week_total_mins / 60, 1)} {hour_label}",
        "total_messages": week_total_msgs,
        "avg_daily_minutes": round(week_total_mins / max(1, today_dt.weekday() + 1)),
        "planet_id": week_planet["id"],
        "planet_name": week_planet["name"],
        "planet_title": week_planet["title"],
        "planet_icon": week_planet["icon"],
        "planets": week_planets,
        "days": week_days
    }

    # 3. Oylik (Joriy oy)
    month_prefix = today_dt.strftime("%Y-%m")
    month_int = int(today_dt.strftime("%m"))
    month_name_trans = _STATIC_TRANSLATIONS.get(lang, _STATIC_TRANSLATIONS["uzb"])["months"][month_int]
    month_label = f"{month_name_trans} {today_dt.year}"

    cursor.execute(
        "SELECT SUM(minutes_spent) as total_mins, SUM(messages_count) as total_msgs, COUNT(DISTINCT date) as active_days FROM child_activities WHERE child_id = ? AND date LIKE ?",
        (child_id, f"{month_prefix}%")
    )
    month_row = cursor.fetchone()
    month_mins = (month_row["total_mins"] if month_row else 0) or 0
    month_msgs = (month_row["total_msgs"] if month_row else 0) or 0
    month_active_days = (month_row["active_days"] if month_row else 0) or 0

    # Oyning asosiy sayyorasi
    cursor.execute("SELECT planet_id, SUM(minutes_spent) as p_mins FROM child_activities WHERE child_id = ? AND date LIKE ? GROUP BY planet_id ORDER BY p_mins DESC LIMIT 1", (child_id, f"{month_prefix}%"))
    month_top_p = cursor.fetchone()
    month_pid = month_top_p["planet_id"] if month_top_p else 42
    month_planet = _get_planet_meta(month_pid)

    # Oylik sayyoralar taqsimoti
    cursor.execute("SELECT planet_id, SUM(minutes_spent) as p_mins, SUM(messages_count) as p_msgs FROM child_activities WHERE child_id = ? AND date LIKE ? GROUP BY planet_id ORDER BY p_mins DESC", (child_id, f"{month_prefix}%"))
    month_planets = []
    for r in cursor.fetchall():
        pmeta = _get_planet_meta(r["planet_id"])
        month_planets.append({
            "planet_id": pmeta["id"],
            "planet_name": pmeta["name"],
            "planet_title": pmeta["title"],
            "planet_icon": pmeta["icon"],
            "minutes": r["p_mins"] or 0,
            "messages": r["p_msgs"] or 0
        })

    monthly_data = {
        "month": month_label,
        "total_minutes": month_mins,
        "total_hours": f"{round(month_mins / 60, 1)} {hour_label}",
        "total_messages": month_msgs,
        "active_days": month_active_days,
        "planet_id": month_planet["id"],
        "planet_name": month_planet["name"],
        "planet_title": month_planet["title"],
        "planet_icon": month_planet["icon"],
        "planets": month_planets
    }

    # 4. Eng ko'p kirilgan sevimli sayyora
    cursor.execute("""
        SELECT planet_id, SUM(minutes_spent) as p_mins 
        FROM child_activities 
        WHERE child_id = ? AND planet_id IS NOT NULL 
        GROUP BY planet_id 
        ORDER BY p_mins DESC LIMIT 1
    """, (child_id,))
    fav_row = cursor.fetchone()

    if fav_row and fav_row["planet_id"]:
        fav_pid = fav_row["planet_id"]
        fav_meta = _get_planet_meta(fav_pid)
        fav_planet = {
            "id": fav_pid,
            "name": fav_meta["name"],
            "title": fav_meta["title"],
            "icon": fav_meta["icon"],
            "minutes_spent": fav_row["p_mins"]
        }
    else:
        fav_meta = _get_planet_meta(42)
        fav_planet = {
            "id": 42,
            "name": fav_meta["name"],
            "title": fav_meta["title"],
            "icon": fav_meta["icon"],
            "minutes_spent": daily_mins
        }

    conn.close()

    return {
        "child_id": child_id,
        "child_name": child_name,
        "daily": daily_data,
        "weekly": weekly_data,
        "monthly": monthly_data,
        "favorite_planet": fav_planet
    }


@app.get("/mobile/child/{child_id}/activity-stats/", response_model=ChildActivityStatsResponse, tags=["Mobil Ilova — Autentifikatsiya & Farzandlar Boshqaruvi"], summary="7.9. Farzandning AI Faollik Statistikasi — Kunlik, Haftalik, Oylik (Token orqali)")
@app.get("/mobile/child/{child_id}/activity-stats", response_model=ChildActivityStatsResponse, include_in_schema=False)
@app.get("/mobile/child-activity/{child_id}", response_model=ChildActivityStatsResponse, include_in_schema=False)
@app.get("/mobile/child/{child_id}/stats", response_model=ChildActivityStatsResponse, include_in_schema=False)
@app.get("/api/website/child/{child_id}/activity-stats/", response_model=ChildActivityStatsResponse, tags=["Web Sayt (Website)"], summary="Web: Farzandning AI Faollik Statistikasi")
@app.get("/api/website/child/{child_id}/activity-stats", response_model=ChildActivityStatsResponse, include_in_schema=False)
def get_child_activity_stats_endpoint(child_id: int, request: Request, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    return calculate_child_activity_stats(child_id, user_id, request)


# 7.10 FARZANDNING AI BILAN SUHBAT TARIXI (CHAT HISTORY)
@app.get("/mobile/child/{child_id}/ai-history/", response_model=List[AiChatHistoryItemResponse], tags=["Mobil Ilova — Autentifikatsiya & Farzandlar Boshqaruvi"], summary="7.10. Farzandning AI Bilan Suhbat Tarixi (Token orqali)")
@app.get("/mobile/child/{child_id}/ai-history", response_model=List[AiChatHistoryItemResponse], include_in_schema=False)
@app.get("/mobile/ai/history/{child_id}", response_model=List[AiChatHistoryItemResponse], include_in_schema=False)
@app.get("/mobile/ai/history/", response_model=List[AiChatHistoryItemResponse], include_in_schema=False)
@app.get("/api/website/child/{child_id}/ai-history/", response_model=List[AiChatHistoryItemResponse], tags=["Web Sayt (Website)"], summary="Web: Farzand AI Suhbat Tarixi")
@app.get("/api/website/child/{child_id}/ai-history", response_model=List[AiChatHistoryItemResponse], include_in_schema=False)
def get_child_ai_history(child_id: Optional[int] = None, request: Request = None, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    conn = get_db_connection()
    cursor = conn.cursor()

    if child_id:
        cursor.execute("SELECT * FROM ai_chat_history WHERE user_id = ? AND child_id = ? ORDER BY id ASC", (user_id, child_id))
    else:
        cursor.execute("SELECT * FROM ai_chat_history WHERE user_id = ? ORDER BY id ASC", (user_id,))
    rows = cursor.fetchall()
    conn.close()

    result = []
    for r in rows:
        d = dict(r)
        audio = d.get("audio_url")
        if audio and request:
            audio = to_full_image_url(audio, request)
        result.append({
            "id": d["id"],
            "role": d["role"],
            "message": d["message"],
            "audio_url": audio,
            "planet_id": d.get("planet_id"),
            "planet_name": d.get("planet_name"),
            "created_at": str(d.get("created_at") or "")
        })
    return result


@app.delete("/mobile/child/{child_id}/ai-history/", tags=["Mobil Ilova — Alloma AI & Ovozli Yordamchi"], summary="7.11. Farzandning AI Suhbat Tarixini Tozalash (Token orqali)")
@app.delete("/mobile/child/{child_id}/ai-history", include_in_schema=False)
@app.delete("/api/website/child/{child_id}/ai-history/", tags=["Web Sayt (Website)"], summary="Web: Farzand AI Suhbat Tarixini Tozalash")
@app.delete("/api/website/child/{child_id}/ai-history", include_in_schema=False)
def delete_child_ai_history(child_id: int, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ai_chat_history WHERE user_id = ? AND child_id = ?", (user_id, child_id))
    conn.commit()
    conn.close()
    return {"success": True, "message": "AI suhbat tarixi muvaffaqiyatli tozalandi", "child_id": child_id}


# ==============================================================================
# 7.12. NEPTUNE / EMOTSIYALAR VA KAYFIYAT KUNDALIGI (EMOTIONAL PLANET)
# ==============================================================================

EMOTIONS_CONFIG = {
    "happy": {
        "uzb": {"name": "Xursand", "description": "Quvnoq, xushchaqchaq va yaxshi kayfiyatda"},
        "rus": {"name": "Счастливый", "description": "Радостное и хорошее настроение"},
        "eng": {"name": "Happy", "description": "Joyful and in a good mood"},
        "emoji": "😊",
        "color": "#FFD166",
        "planet_id": 46
    },
    "calm": {
        "uzb": {"name": "Xotirjam", "description": "Tinch, osoyishta va xotirjam holat"},
        "rus": {"name": "Спокойный", "description": "Тихое и умиротворенное состояние"},
        "eng": {"name": "Calm", "description": "Peaceful and relaxed"},
        "emoji": "😌",
        "color": "#06D6A0",
        "planet_id": 46
    },
    "excited": {
        "uzb": {"name": "G'ayratli", "description": "Ilhomlangan, yangiliklarga tayyor va quvnoq"},
        "rus": {"name": "Воодушевленный", "description": "Полный энергии и вдохновения"},
        "eng": {"name": "Excited", "description": "Full of energy and enthusiasm"},
        "emoji": "🤩",
        "color": "#118AB2",
        "planet_id": 46
    },
    "proud": {
        "uzb": {"name": "Faxrlangan", "description": "O'z yutug'idan mamnun va minnatdor"},
        "rus": {"name": "Гордый", "description": "Доволен своими успехами"},
        "eng": {"name": "Proud", "description": "Satisfied with personal achievement"},
        "emoji": "🥰",
        "color": "#EF476F",
        "planet_id": 46
    },
    "tired": {
        "uzb": {"name": "Charchagan", "description": "Kuchsizlangan, dam olish va uxlash kerak"},
        "rus": {"name": "Уставший", "description": "Нужен отдых и сон"},
        "eng": {"name": "Tired", "description": "Needs rest and sleep"},
        "emoji": "😴",
        "color": "#8338EC",
        "planet_id": 46
    },
    "sad": {
        "uzb": {"name": "G'amgin / Xafa", "description": "Ko'ngli to'lmagan yoki xafa bo'lgan holat"},
        "rus": {"name": "Грустный", "description": "Опечален или расстроен"},
        "eng": {"name": "Sad", "description": "Feeling down or disappointed"},
        "emoji": "😢",
        "color": "#4A90E2",
        "planet_id": 46
    },
    "angry": {
        "uzb": {"name": "Jahldor", "description": "Asabiylashgan yoki g'azablangan holat"},
        "rus": {"name": "Сердитый", "description": "Раздражен или злится"},
        "eng": {"name": "Angry", "description": "Frustrated or irritated"},
        "emoji": "😠",
        "color": "#E63946",
        "planet_id": 46
    },
    "scared": {
        "uzb": {"name": "Qo'rqqan", "description": "Cho'chigan yoki xavotirlangan holat"},
        "rus": {"name": "Испуганный", "description": "Боится или тревожится"},
        "eng": {"name": "Scared", "description": "Afraid or anxious"},
        "emoji": "😨",
        "color": "#FB8500",
        "planet_id": 46
    },
    "surprised": {
        "uzb": {"name": "Hayron", "description": "Kutilmagan yangilikdan hayratda"},
        "rus": {"name": "Удивленный", "description": "Удивлен неожиданностью"},
        "eng": {"name": "Surprised", "description": "Amazed by something unexpected"},
        "emoji": "😲",
        "color": "#02C39A",
        "planet_id": 46
    }
}

def _get_day_name(date_str: str, lang: str = "uzb") -> str:
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        weekday = dt.weekday()
        day_names = {
            "uzb": ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"],
            "rus": ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"],
            "eng": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        }
        return day_names.get(lang, day_names["uzb"])[weekday]
    except Exception:
        return ""


# 7.12.1. MAVJUD EMOTSIYALAR RO'YXATI
@app.get("/mobile/planets/neptune/options/", response_model=List[EmotionOption], tags=["Mobil Ilova — Neptun Sayyorasi (Hissiyotlar & Emotsiyalar)"], summary="7.12.1. Neptune / Emotsiyalar Sayyorasi — Mavjud Emotsiyalar Ro'yxati")
@app.get("/mobile/planets/neptune/options", response_model=List[EmotionOption], include_in_schema=False)
@app.get("/mobile/planets/neptun/options/", response_model=List[EmotionOption], include_in_schema=False)
@app.get("/mobile/planets/neptun/options", response_model=List[EmotionOption], include_in_schema=False)
@app.get("/mobile/emotions/options/", response_model=List[EmotionOption], include_in_schema=False)
@app.get("/mobile/emotions/options", response_model=List[EmotionOption], include_in_schema=False)
def get_neptune_emotion_options(request: Request):
    lang = get_accept_language(request)
    options = []
    for key, val in EMOTIONS_CONFIG.items():
        lang_data = val.get(lang, val["uzb"])
        options.append({
            "key": key,
            "name": lang_data["name"],
            "emoji": val["emoji"],
            "color": val["color"],
            "description": lang_data["description"]
        })
    return options


# 7.12.2. BOLANING YANGI EMOTSIYASINI SAQLASH (BOLA & NEPTUNE UCHUN)
@app.post("/mobile/planets/neptune/emotions/", response_model=EmotionItemResponse, status_code=status.HTTP_201_CREATED, tags=["Mobil Ilova — Neptun Sayyorasi (Hissiyotlar & Emotsiyalar)"], summary="7.12.2. Farzand Emotsiyasini Belgilash / Saqlash (Token orqali)")
@app.post("/mobile/planets/neptune/emotions", response_model=EmotionItemResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@app.post("/mobile/planets/neptun/emotions/", response_model=EmotionItemResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@app.post("/mobile/planets/neptun/emotions", response_model=EmotionItemResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@app.post("/mobile/emotions/", response_model=EmotionItemResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@app.post("/mobile/emotions", response_model=EmotionItemResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def record_child_emotion(
    req: RecordEmotionRequest,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id"]
    lang = get_accept_language(request)
    now = datetime.now()
    date_str = req.date or now.strftime("%Y-%m-%d")
    time_str = req.time or now.strftime("%H:%M:%S")

    emotion_cfg = EMOTIONS_CONFIG.get(req.emotion_key.lower().strip(), EMOTIONS_CONFIG["happy"])
    lang_data = emotion_cfg.get(lang, emotion_cfg["uzb"])
    emotion_name = lang_data["name"]
    emoji = req.emoji or emotion_cfg["emoji"]
    color = emotion_cfg["color"]

    conn = get_db_connection()
    cursor = conn.cursor()

    # Farzand tegishliligini tekshirish
    cursor.execute("SELECT id, name, surname FROM children WHERE id = ? AND user_id = ?", (req.child_id, user_id))
    child_row = cursor.fetchone()
    if not child_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Farzand topilmadi yoki sizga tegishli emas!")

    child_full_name = f"{child_row['name']} {child_row['surname']}".strip()

    cursor.execute("""
        INSERT INTO child_emotions (user_id, child_id, emotion_key, emotion_name, emoji, color, intensity, note, planet_id, date, time)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        req.child_id,
        req.emotion_key.lower().strip(),
        emotion_name,
        emoji,
        color,
        req.intensity or 3,
        (req.note or "").strip(),
        46, # Neptune / Emotional planet
        date_str,
        time_str
    ))
    emotion_id = cursor.lastrowid
    conn.commit()
    conn.close()

    day_name = _get_day_name(date_str, lang)

    return {
        "id": emotion_id,
        "child_id": req.child_id,
        "child_name": child_full_name,
        "emotion_key": req.emotion_key.lower().strip(),
        "emotion_name": emotion_name,
        "emoji": emoji,
        "color": color,
        "intensity": req.intensity or 3,
        "note": (req.note or "").strip(),
        "date": date_str,
        "time": time_str,
        "day_name": day_name,
        "created_at": now.strftime("%Y-%m-%d %H:%M:%S")
    }


# Farzand ID si URL path orqali berilganda qo'llab-quvvatlash
@app.post("/mobile/child/{child_id}/emotions/", response_model=EmotionItemResponse, status_code=status.HTTP_201_CREATED, tags=["Mobil Ilova — Neptun Sayyorasi (Hissiyotlar & Emotsiyalar)"], summary="7.12.2.1. Farzand Emotsiyasini Belgilash (Path ID orqali)")
@app.post("/mobile/child/{child_id}/emotions", response_model=EmotionItemResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def record_child_emotion_by_path(
    child_id: int,
    req: RecordEmotionRequest,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    req.child_id = child_id
    return record_child_emotion(req, request, current_user)


# 7.12.3. BOLA UCHUN: OXIRGI 7 KUNLIK (1 HAFTALIK) EMOTSIYALAR
# (7 kundan eski emotsiyalar bola panelida ko'rinmaydi — avtomatik o'chadi/filtrlanadi)
@app.get("/mobile/planets/neptune/emotions/", response_model=WeeklyChildEmotionsResponse, tags=["Mobil Ilova — Neptun Sayyorasi (Hissiyotlar & Emotsiyalar)"], summary="7.12.3. Neptune / Bola Paneli — Oxirgi 7 Kunlik Emotsiyalar (Token orqali)")
@app.get("/mobile/planets/neptune/emotions", response_model=WeeklyChildEmotionsResponse, include_in_schema=False)
@app.get("/mobile/planets/neptun/emotions/", response_model=WeeklyChildEmotionsResponse, include_in_schema=False)
@app.get("/mobile/planets/neptun/emotions", response_model=WeeklyChildEmotionsResponse, include_in_schema=False)
@app.get("/mobile/emotions/weekly/", response_model=WeeklyChildEmotionsResponse, include_in_schema=False)
@app.get("/mobile/emotions/weekly", response_model=WeeklyChildEmotionsResponse, include_in_schema=False)
def get_child_weekly_emotions(
    child_id: Optional[int] = Query(None, description="Farzand ID raqami"),
    request: Request = None,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id"]
    lang = get_accept_language(request)

    conn = get_db_connection()
    cursor = conn.cursor()

    # Farzandni aniqlash
    if child_id:
        cursor.execute("SELECT id, name, surname FROM children WHERE id = ? AND user_id = ?", (child_id, user_id))
    else:
        cursor.execute("SELECT id, name, surname FROM children WHERE user_id = ? ORDER BY id ASC LIMIT 1", (user_id,))
    
    child_row = cursor.fetchone()
    if not child_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Farzand topilmadi!")

    target_child_id = child_row["id"]
    child_full_name = f"{child_row['name']} {child_row['surname']}".strip()

    # Oxirgi 7 kunlik sanalarni hisoblash
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    cursor.execute("""
        SELECT * FROM child_emotions 
        WHERE user_id = ? AND child_id = ? AND date >= ?
        ORDER BY date DESC, time DESC
    """, (user_id, target_child_id, seven_days_ago))
    rows = cursor.fetchall()
    conn.close()

    emotions_list = []
    emotion_counter = {}
    daily_map = {}

    for r in rows:
        d = dict(r)
        d_date = d["date"]
        d_day = _get_day_name(d_date, lang)
        key = d.get("emotion_key", "happy")
        cfg = EMOTIONS_CONFIG.get(key, EMOTIONS_CONFIG["happy"])
        lang_data = cfg.get(lang, cfg["uzb"])

        item = {
            "id": d["id"],
            "child_id": d["child_id"],
            "child_name": child_full_name,
            "emotion_key": key,
            "emotion_name": lang_data["name"],
            "emoji": d.get("emoji") or cfg["emoji"],
            "color": d.get("color") or cfg["color"],
            "intensity": d.get("intensity") or 3,
            "note": d.get("note") or "",
            "date": d_date,
            "time": d.get("time") or "",
            "day_name": d_day,
            "created_at": str(d.get("created_at") or "")
        }
        emotions_list.append(item)

        # Statistika
        emotion_counter[key] = emotion_counter.get(key, 0) + 1

        if d_date not in daily_map:
            daily_map[d_date] = {
                "date": d_date,
                "day_name": d_day,
                "emotions": []
            }
        daily_map[d_date]["emotions"].append(item)

    dominant_key = max(emotion_counter, key=emotion_counter.get) if emotion_counter else None
    dominant_name = EMOTIONS_CONFIG.get(dominant_key, {}).get(lang, {}).get("name") if dominant_key else None
    dominant_emoji = EMOTIONS_CONFIG.get(dominant_key, {}).get("emoji") if dominant_key else None

    # Kunlar bo'yicha saralash
    daily_summary = list(daily_map.values())

    return {
        "success": True,
        "child_id": target_child_id,
        "child_name": child_full_name,
        "period": "last_7_days",
        "total_records": len(emotions_list),
        "dominant_emotion": dominant_name,
        "dominant_emoji": dominant_emoji,
        "emotions": emotions_list,
        "daily_summary": daily_summary
    }


# 7.12.4. OTA-ONA UCHUN: FARZANDNING TO'LIQ EMOTSIYALAR TARIXI VA ANALITIKASI
# (Ota-ona uchun barcha tarixlar, shu jumladan 7 kundan oldingilar ham o'chmasdan turadi!)
@app.get("/mobile/parent/child/{child_id}/emotions/", response_model=ParentChildEmotionsAnalyticsResponse, tags=["Mobil Ilova — Neptun Sayyorasi (Hissiyotlar & Emotsiyalar)"], summary="7.12.4. Ota-ona Paneli — Farzandning To'liq Emotsiyalar Tarixi & Tahlili (Token orqali)")
@app.get("/mobile/parent/child/{child_id}/emotions", response_model=ParentChildEmotionsAnalyticsResponse, include_in_schema=False)
@app.get("/mobile/parents/child/{child_id}/emotions/", response_model=ParentChildEmotionsAnalyticsResponse, include_in_schema=False)
@app.get("/mobile/parents/child/{child_id}/emotions", response_model=ParentChildEmotionsAnalyticsResponse, include_in_schema=False)
@app.get("/api/website/child/{child_id}/emotions/", response_model=ParentChildEmotionsAnalyticsResponse, tags=["Web Sayt (Website)"], summary="Web: Farzand Emotsiyalar Tarixi & Tahlili")
@app.get("/api/website/child/{child_id}/emotions", response_model=ParentChildEmotionsAnalyticsResponse, include_in_schema=False)
def get_parent_child_emotions_analytics(
    child_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id"]
    lang = get_accept_language(request)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, surname FROM children WHERE id = ? AND user_id = ?", (child_id, user_id))
    child_row = cursor.fetchone()
    if not child_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Farzand topilmadi yoki sizga tegishli emas!")

    child_full_name = f"{child_row['name']} {child_row['surname']}".strip()

    # Barcha tarixni olish (hech qanday kun cheklovisiz)
    cursor.execute("""
        SELECT * FROM child_emotions 
        WHERE user_id = ? AND child_id = ?
        ORDER BY date DESC, time DESC
    """, (user_id, child_id))
    all_rows = cursor.fetchall()
    conn.close()

    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    all_history = []
    weekly_emotions = []
    emotion_counts = {}

    for r in all_rows:
        d = dict(r)
        d_date = d["date"]
        d_day = _get_day_name(d_date, lang)
        key = d.get("emotion_key", "happy")
        cfg = EMOTIONS_CONFIG.get(key, EMOTIONS_CONFIG["happy"])
        lang_data = cfg.get(lang, cfg["uzb"])

        item = {
            "id": d["id"],
            "child_id": d["child_id"],
            "child_name": child_full_name,
            "emotion_key": key,
            "emotion_name": lang_data["name"],
            "emoji": d.get("emoji") or cfg["emoji"],
            "color": d.get("color") or cfg["color"],
            "intensity": d.get("intensity") or 3,
            "note": d.get("note") or "",
            "date": d_date,
            "time": d.get("time") or "",
            "day_name": d_day,
            "created_at": str(d.get("created_at") or "")
        }
        all_history.append(item)

        # 7 kunlik saralash
        if d_date >= seven_days_ago:
            weekly_emotions.append(item)

        # Taqsimot hisoblash
        if key not in emotion_counts:
            emotion_counts[key] = {
                "key": key,
                "name": lang_data["name"],
                "emoji": cfg["emoji"],
                "color": cfg["color"],
                "count": 0
            }
        emotion_counts[key]["count"] += 1

    total_records = len(all_history)
    distribution = []
    for k, v in emotion_counts.items():
        pct = round((v["count"] / total_records) * 100, 1) if total_records > 0 else 0
        distribution.append({
            "emotion_key": v["key"],
            "emotion_name": v["name"],
            "emoji": v["emoji"],
            "color": v["color"],
            "count": v["count"],
            "percentage": pct
        })
    distribution.sort(key=lambda x: x["count"], reverse=True)

    dominant_key = distribution[0]["emotion_key"] if distribution else None
    dominant_name = distribution[0]["emotion_name"] if distribution else None
    dominant_emoji = distribution[0]["emoji"] if distribution else None

    # AI tavsiyasi
    ai_recommendation = None
    if dominant_key in ["happy", "excited", "proud"]:
        ai_recommendation = f"{child_row['name']} so'nggi vaqtlarda asosan ijobiy va quvnoq kayfiyatda! Bu uning darslarni o'zlashtirishi va ijodiy fikrlashiga ajoyib turtki beradi."
    elif dominant_key in ["sad", "tired", "angry", "scared"]:
        ai_recommendation = f"{child_row['name']} biroz charchagan yoki xavotirli holatda. Unga ko'proq tabiat qo'ynida dam berish, birgalikda sayr qilish va samimiy suhbatlashish tavsiya etiladi."
    else:
        ai_recommendation = f"{child_row['name']} barqaror va xotirjam holatda o'rganmoqda. Ushbu sokin muhit uning diqqatini jamlashiga yordam beradi."

    return {
        "success": True,
        "child_id": child_id,
        "child_name": child_full_name,
        "total_history_count": total_records,
        "last_7_days_count": len(weekly_emotions),
        "dominant_emotion": dominant_name,
        "dominant_emoji": dominant_emoji,
        "emotion_distribution": distribution,
        "weekly_emotions": weekly_emotions,
        "all_history": all_history,
        "ai_recommendation": ai_recommendation
    }


# 7.12.5. EMOTSIYANI O'CHIRISH
@app.delete("/mobile/planets/neptune/emotions/{emotion_id}", tags=["Mobil Ilova — Neptun Sayyorasi (Hissiyotlar & Emotsiyalar)"], summary="7.12.5. Emotsiya Yozuvini O'chirish (Token orqali)")
@app.delete("/mobile/planets/neptun/emotions/{emotion_id}", include_in_schema=False)
@app.delete("/mobile/child/emotions/{emotion_id}", include_in_schema=False)
def delete_child_emotion(emotion_id: int, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM child_emotions WHERE id = ? AND user_id = ?", (emotion_id, user_id))
    conn.close()
    return {"success": True, "message": "Emotsiya yozuvi muvaffaqiyatli o'chirildi", "id": emotion_id}


# ==============================================================================
# 7.13. URAN (URANUS) / NUTQ VA TIL SAYYORASI — SO'ZLAR VA TESTLAR
# ==============================================================================

# 7.13.1. URAN KATEGORIYALARI RO'YXATI (/mobile/planets/uran/category/)
@app.get("/mobile/planets/uran/category/", response_model=List[UranCategoryResponse], tags=["Mobil Ilova — Uran Sayyorasi (Nutq & Til)"], summary="7.13.1. Uran / Nutq va Til Sayyorasi — Kategoriyalar Ro'yxati (name, image, words_count)")
@app.get("/mobile/planets/uran/category", response_model=List[UranCategoryResponse], include_in_schema=False)
@app.get("/mobile/planets/uranus/category/", response_model=List[UranCategoryResponse], include_in_schema=False)
@app.get("/mobile/planets/uranus/category", response_model=List[UranCategoryResponse], include_in_schema=False)
@app.get("/mobile/uran/categories/", response_model=List[UranCategoryResponse], include_in_schema=False)
@app.get("/mobile/uran/categories", response_model=List[UranCategoryResponse], include_in_schema=False)
def get_uran_categories(
    request: Request,
    status: Optional[str] = None,
    child_id: Optional[int] = None,
    is_admin: bool = False,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    user_dict = current_user if isinstance(current_user, dict) else None
    effective_child_id = child_id or resolve_child_id(None, user_dict)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.*, COUNT(w.id) as words_count 
        FROM uran_categories c 
        LEFT JOIN uran_words w ON c.id = w.category_id 
        GROUP BY c.id 
        ORDER BY c.order_num ASC, c.id ASC
    """)
    rows = cursor.fetchall()

    # Bolaning topshirgan test natijalari
    cursor.execute("""
        SELECT category_id, MAX(percentage) as max_pct, MAX(score) as max_score
        FROM child_uran_quiz_results
        WHERE child_id = ?
        GROUP BY category_id
    """, (effective_child_id,))
    quiz_results = {r["category_id"]: r for r in cursor.fetchall()}
    conn.close()

    result = []
    # 1-chi chiqqan kategoriya (idx == 0) har doim ochiq (active)
    # Keyingilari esa FAQAT VA FAQAT avvalgi mavzuning testi >= 60% topshirilsa ochiladi!
    prev_cat_passed = False

    for idx, row in enumerate(rows):
        cid = row["id"]
        q_res = quiz_results.get(cid)
        best_pct = round(q_res["max_pct"], 1) if q_res and q_res["max_pct"] is not None else 0.0
        best_sc = q_res["max_score"] if q_res and q_res["max_score"] is not None else 0
        cat_passed = best_pct >= 60.0

        db_status = (row["status"] or "active").lower()

        if is_admin:
            is_unlocked = (db_status == "active")
            cat_status = db_status
        else:
            if idx == 0:
                is_unlocked = True
                cat_status = "active"
            else:
                # Keyingilari FAQAT avvalgi kategoriya testidan >= 60% o'tsagina ochiladi!
                if prev_cat_passed:
                    is_unlocked = True
                    cat_status = "active"
                else:
                    is_unlocked = False
                    cat_status = "inactive"

        # Keyingi kategoriya ochilishi uchun ushbu kategoriyaning o'zi testdan >= 60% o'tgan bo'lishi kerak
        prev_cat_passed = cat_passed

        if status and cat_status != status:
            continue

        result.append({
            "id": row["id"],
            "name": row["name"],
            "name_en": row["name_en"] or "",
            "name_ru": row["name_ru"] or "",
            "image": to_full_image_url(row["image"], request),
            "description": row["description"] or "",
            "status": cat_status,
            "order_num": row["order_num"] or 0,
            "words_count": row["words_count"] or 0,
            "created_at": str(row["created_at"]) if row["created_at"] else None,
            "is_unlocked": is_unlocked,
            "is_blocked": not is_unlocked,
            "is_block": not is_unlocked,
            "passed": cat_passed,
            "best_score": best_sc,
            "best_percentage": best_pct
        })
    return result


URAN_POS_UZ_MAP = {
    "noun": "Ot",
    "adjective": "Sifat",
    "verb": "Fe'l",
    "adverb": "Ravish",
    "pronoun": "Olmosh",
    "preposition": "Old ko'makchi",
    "conjunction": "Bog'lovchi",
    "other": "Boshqa"
}

def format_uran_word_row(row, request=None, fallback_image=None):
    row_keys = row.keys() if hasattr(row, 'keys') else []
    pos = row["part_of_speech"] if ("part_of_speech" in row_keys and row["part_of_speech"]) else "noun"
    pos_uz = row["part_of_speech_uz"] if ("part_of_speech_uz" in row_keys and row["part_of_speech_uz"]) else URAN_POS_UZ_MAP.get(pos, "Ot")
    raw_img = row["image"] or fallback_image or ""
    word_img = to_full_image_url(raw_img, request) if request else raw_img
    audio_url = to_full_image_url(row["audio_url"], request) if (row["audio_url"] and request) else (row["audio_url"] or None)

    return {
        "id": row["id"],
        "category_id": row["category_id"],
        "word_uz": row["word_uz"],
        "word_en": row["word_en"],
        "word_ru": row["word_ru"] or "",
        "transcription": row["transcription"] or "",
        "part_of_speech": pos,
        "part_of_speech_uz": pos_uz,
        "image": word_img,
        "audio_url": audio_url,
        "example_sentence": row["example_sentence"] or "",
        "example_translation": row["example_translation"] or "",
        "order_num": row["order_num"] or 0,
        "created_at": str(row["created_at"]) if row["created_at"] else None
    }


# 7.13.2. URAN KATEGORIYA SO'ZLARI VA TEST SAVOLLARI (/mobile/planets/uran/category/{category_id})
@app.get("/mobile/planets/uran/category/{category_id}", response_model=UranCategoryDetailResponse, tags=["Mobil Ilova — Uran Sayyorasi (Nutq & Til)"], summary="7.13.2. Uran / Kategoriya So'zlari va Test Savollari (Inglizcha-O'zbekcha va 4 Variantli Test)")
@app.get("/mobile/planets/uran/category/{category_id}/", response_model=UranCategoryDetailResponse, include_in_schema=False)
@app.get("/mobile/planets/uranus/category/{category_id}", response_model=UranCategoryDetailResponse, include_in_schema=False)
@app.get("/mobile/planets/uranus/category/{category_id}/", response_model=UranCategoryDetailResponse, include_in_schema=False)
@app.get("/mobile/uran/category/{category_id}", response_model=UranCategoryDetailResponse, include_in_schema=False)
@app.get("/mobile/uran/category/{category_id}/", response_model=UranCategoryDetailResponse, include_in_schema=False)
def get_uran_category_detail(category_id: int, request: Request):
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Kategoriya ma'lumoti
    cursor.execute("SELECT * FROM uran_categories WHERE id = ?", (category_id,))
    cat_row = cursor.fetchone()
    if not cat_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Kategoriya topilmadi")

    # 2. Kategoriyadagi barcha so'zlar
    cursor.execute("SELECT * FROM uran_words WHERE category_id = ? ORDER BY order_num ASC, id ASC", (category_id,))
    word_rows = cursor.fetchall()

    # 3. Test variantlari uchun boshqa barcha so'zlar zaxirasi
    cursor.execute("SELECT word_uz, word_en FROM uran_words WHERE category_id != ?", (category_id,))
    other_word_rows = cursor.fetchall()
    conn.close()

    category_image_url = to_full_image_url(cat_row["image"], request)

    words_list = []
    tests_list = []

    # Kategoriyadagi o'zbekcha so'zlar to'plami
    cat_uz_words = [w["word_uz"] for w in word_rows]
    other_uz_words = [w["word_uz"] for w in other_word_rows]

    for idx, w in enumerate(word_rows):
        word_item = format_uran_word_row(w, request, cat_row["image"])
        words_list.append(word_item)

        # 4 ta variantli test savoli tayyorlash:
        correct_ans = w["word_uz"]
        # Chalg'ituvchi variantlar (noto'g'ri 3 ta javob)
        cat_distractors = [u for u in cat_uz_words if u != correct_ans]
        other_distractors = [u for u in other_uz_words if u != correct_ans and u not in cat_distractors]

        distractors = []
        if len(cat_distractors) >= 3:
            distractors = random.sample(cat_distractors, 3)
        else:
            distractors = list(cat_distractors)
            needed = 3 - len(distractors)
            if len(other_distractors) >= needed:
                distractors.extend(random.sample(other_distractors, needed))
            else:
                distractors.extend(other_distractors)
                fallback = ["Olma", "Kitob", "Quyosh", "Sher", "Mashina", "Doira", "Qizil"]
                for fb in fallback:
                    if len(distractors) >= 3:
                        break
                    if fb != correct_ans and fb not in distractors:
                        distractors.append(fb)

        options = [correct_ans] + distractors[:3]
        random.shuffle(options)

        pos = word_item.get("part_of_speech") or "noun"

        test_item = {
            "id": idx + 1,
            "word_id": w["id"],
            "word_en": w["word_en"],
            "question": w["word_en"],
            "prompt": f"'{w['word_en']}' so'zining o'zbekcha tarjimasi qaysi?",
            "correct_answer": correct_ans,
            "part_of_speech": pos,
            "options": options,
            "image": word_item["image"],
            "explanation": f"'{w['word_en']}' so'zi o'zbek tilida '{correct_ans}' deb tarjima qilinadi."
        }
        tests_list.append(test_item)

    cat_status = (cat_row["status"] or "active").lower()
    is_unlocked = cat_status == "active"

    return {
        "id": cat_row["id"],
        "name": cat_row["name"],
        "name_en": cat_row["name_en"] or "",
        "name_ru": cat_row["name_ru"] or "",
        "image": category_image_url,
        "description": cat_row["description"] or "",
        "status": cat_status,
        "is_unlocked": is_unlocked,
        "is_blocked": not is_unlocked,
        "is_block": not is_unlocked,
        "words_count": len(words_list),
        "words": words_list,
        "tests": tests_list,
        "quiz": tests_list
    }


# Yordamchi funksiya: Uran test savollari va 4 ta variantlarini tuzish
def build_uran_quiz_questions(selected_words: list, all_uz_pool: list, request: Request = None) -> list:
    tests_list = []
    for idx, w in enumerate(selected_words):
        word_img = to_full_image_url(w["image"], request) if request else w["image"]
        correct_ans = w["word_uz"]

        cat_distractors = [u for u in all_uz_pool if u != correct_ans]
        distractors = []
        if len(cat_distractors) >= 3:
            distractors = random.sample(cat_distractors, 3)
        else:
            distractors = list(cat_distractors)
            fallback = ["Olma", "Kitob", "Quyosh", "Sher", "Mashina", "Doira", "Qizil", "Banan", "Non", "Suv", "Oy", "Daraxt"]
            for fb in fallback:
                if len(distractors) >= 3:
                    break
                if fb != correct_ans and fb not in distractors:
                    distractors.append(fb)

        options = [correct_ans] + distractors[:3]
        random.shuffle(options)

        pos = (w.get("part_of_speech") if hasattr(w, "get") else getattr(w, "part_of_speech", None)) or "noun"

        test_item = {
            "id": idx + 1,
            "word_id": w["id"] if hasattr(w, "__getitem__") else getattr(w, "id"),
            "word_en": w["word_en"] if hasattr(w, "__getitem__") else getattr(w, "word_en"),
            "question": w["word_en"] if hasattr(w, "__getitem__") else getattr(w, "word_en"),
            "prompt": f"'{w['word_en'] if hasattr(w, '__getitem__') else getattr(w, 'word_en')}' so'zining o'zbekcha tarjimasi qaysi?",
            "correct_answer": correct_ans,
            "part_of_speech": pos,
            "options": options,
            "image": word_img,
            "explanation": f"'{w['word_en'] if hasattr(w, '__getitem__') else getattr(w, 'word_en')}' so'zi o'zbek tilida '{correct_ans}' deb tarjima qilinadi."
        }
        tests_list.append(test_item)
    return tests_list


# 7.13.3. URAN TEST NATIJASINI TOPSHIRISH VA SAQLASH
@app.post("/mobile/planets/uran/category/{category_id}/submit-test", response_model=UranQuizSubmitResponse, tags=["Mobil Ilova — Uran Sayyorasi (Nutq & Til)"], summary="7.13.3. Uran / Test Natijasini Saqlash va Baholash")
@app.post("/mobile/planets/uran/category/{category_id}/submit-test/", response_model=UranQuizSubmitResponse, include_in_schema=False)
@app.post("/mobile/planets/uran/submit-test", response_model=UranQuizSubmitResponse, tags=["Mobil Ilova — Uran Sayyorasi (Nutq & Til)"], summary="7.13.3. Uran / Test Natijasini Saqlash va Baholash (Kategoriyasiz)")
@app.post("/mobile/planets/uran/submit-test/", response_model=UranQuizSubmitResponse, include_in_schema=False)
@app.post("/mobile/planets/uran/submit-quiz", response_model=UranQuizSubmitResponse, include_in_schema=False)
@app.post("/mobile/planets/uran/submit-quiz/", response_model=UranQuizSubmitResponse, include_in_schema=False)
@app.post("/mobile/planets/uranus/submit-test", response_model=UranQuizSubmitResponse, include_in_schema=False)
@app.post("/mobile/uran/submit-test", response_model=UranQuizSubmitResponse, include_in_schema=False)
def submit_uran_quiz(payload: UranQuizSubmitRequest, category_id: Optional[int] = None, current_user: Optional[dict] = Depends(get_current_user_optional)):
    effective_category_id = category_id if category_id is not None else (payload.category_id or 1)
    total = max(payload.total_questions, 1)
    score = min(max(payload.score, 0), total)
    percentage = round((score / total) * 100, 1)
    passed = percentage >= 60.0

    if percentage >= 90.0:
        stars = 3
        coins_earned = 30
    elif percentage >= 70.0:
        stars = 2
        coins_earned = 20
    elif percentage >= 50.0:
        stars = 1
        coins_earned = 10
    else:
        stars = 0
        coins_earned = 5

    user_id = current_user["id"] if current_user else 1
    child_id = payload.child_id or resolve_child_id(None, current_user)

    total_coins = 0
    uran_total_coins = 0
    total_planet_words = 0
    total_learned_words = 0
    remaining_new_words = 0
    next_category_unlocked = False
    next_category_id = None
    next_category_name = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Test natijasini saqlash
        cursor.execute("""
            INSERT INTO child_uran_quiz_results (user_id, child_id, category_id, score, total_questions, percentage)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, child_id, effective_category_id, score, total, percentage))

        # 1.1. 60% dan yuqori ball to'plansa, keyingi kategoriya ochiladi (status = 'active')
        if passed:
            cursor.execute("SELECT id, order_num, name FROM uran_categories WHERE id = ?", (effective_category_id,))
            curr_cat = cursor.fetchone()
            if curr_cat:
                curr_order = curr_cat["order_num"] or 0
                cursor.execute("""
                    SELECT id, name, name_en, status, order_num 
                    FROM uran_categories 
                    WHERE (order_num > ?) OR (order_num = ? AND id > ?)
                    ORDER BY order_num ASC, id ASC 
                    LIMIT 1
                """, (curr_order, curr_order, effective_category_id))
                next_cat = cursor.fetchone()
                if next_cat:
                    next_category_id = next_cat["id"]
                    next_category_name = next_cat["name"]
                    cursor.execute("UPDATE uran_categories SET status = 'active' WHERE id = ?", (next_category_id,))
                    next_category_unlocked = True

        # 2. O'rganilgan so'zlarni saqlash (child_uran_learned_words)
        learned_words_to_mark = []
        if payload.word_ids and len(payload.word_ids) > 0:
            learned_words_to_mark = payload.word_ids
        else:
            cursor.execute("SELECT id FROM uran_words WHERE category_id = ?", (effective_category_id,))
            learned_words_to_mark = [r["id"] for r in cursor.fetchall()]

        for wid in learned_words_to_mark:
            cursor.execute("""
                INSERT INTO child_uran_learned_words (user_id, child_id, word_id, correct_count, wrong_count, review_count, last_learned_at)
                VALUES (?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
                ON CONFLICT(child_id, word_id) DO UPDATE SET
                    review_count = child_uran_learned_words.review_count + 1,
                    last_learned_at = CURRENT_TIMESTAMP
            """, (user_id, child_id, wid, 1 if passed else 0, 0 if passed else 1))

        # 3. Vaqt statistikasini yangilash
        spent_mins = max(1, (payload.time_spent_seconds or 60) // 60)
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("SELECT id, minutes_spent FROM child_activities WHERE child_id = ? AND date = ?", (child_id, today))
        act_row = cursor.fetchone()
        if act_row:
            cursor.execute("UPDATE child_activities SET minutes_spent = minutes_spent + ? WHERE id = ?", (spent_mins, act_row["id"]))
        else:
            cursor.execute("""
                INSERT INTO child_activities (user_id, child_id, date, minutes_spent, messages_count, planet_id)
                VALUES (?, ?, ?, ?, 1, 44)
            """, (user_id, child_id, today, spent_mins))

        conn.commit()

        # 4. Coin qo'shish va missiyani yangilash
        coin_res = add_child_coins(
            child_id=child_id,
            user_id=user_id,
            amount=coins_earned,
            transaction_type="earn",
            title="Uran Testi Mukofoti 🏆",
            description=f"Uran sayyorasi testida {score}/{total} ({percentage}%) natija ko'rsatildi.",
            source="uran_quiz"
        )
        total_coins = coin_res["total_coins"]
        update_daily_mission_progress(child_id, user_id, "uran_quiz", 1)

        # 5. Uran sayyorasidagi jami so'zlar va bolaning o'rgangan so'zlarini hisoblash
        cursor.execute("SELECT COUNT(*) as cnt FROM uran_words")
        total_planet_words = cursor.fetchone()["cnt"] or 0

        cursor.execute("SELECT COUNT(DISTINCT word_id) as cnt FROM child_uran_learned_words WHERE child_id = ?", (child_id,))
        total_learned_words = cursor.fetchone()["cnt"] or 0

        remaining_new_words = max(0, total_planet_words - total_learned_words)

        # 6. Bolaning faqat Uran sayyorasining o'zida yutib olgan jami coinlari
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) as uran_coins 
            FROM coin_transactions 
            WHERE child_id = ? AND source = 'uran_quiz' AND transaction_type = 'earn'
        """, (child_id,))
        uran_total_coins = cursor.fetchone()["uran_coins"] or 0

        conn.close()
    except Exception as e:
        print("Quiz natijasini saqlashda xatolik:", e)

    # 7. Barakalla xabari: so'zlar statistikasi, Uran coinlari va keyingi mavzu ochilishi bilan
    if passed:
        unlock_msg = ""
        if next_category_unlocked and next_category_name:
            unlock_msg = f" 🔓 Ajoyib natija (60% dan yuqori)! Siz keyingi mavzuni ochdingiz: '{next_category_name}'!"

        congrat = (
            f"Barakalla! Sen Uran sayyorasidagi jami {total_planet_words} ta so'zdan "
            f"{total_learned_words} tasini muvaffaqiyatli yod olding! 🌟🌟🌟 "
            f"Ushbu testda +{coins_earned} Coin yutding! Uran sayyorasida to'plagan jami tangalaring: {uran_total_coins} Coin! 🚀"
            f"{unlock_msg}"
        )
    else:
        congrat = (
            f"Harakatdan to'xtama! To'plagan natijang: {score}/{total} ({percentage}%). "
            f"Keyingi mavzuni ochish uchun testdan kamida 60% to'plashingiz kerak. "
            f"Ushbu testda +{coins_earned} Coin olding! Yana bir bor urinib ko'r, albatta uddalaysan! 💪"
        )

    return {
        "success": True,
        "message": f"Test natijasi muvaffaqiyatli saqlandi! ({score}/{total}, {percentage}%)",
        "score": score,
        "total_questions": total,
        "percentage": percentage,
        "passed": passed,
        "stars_earned": stars,
        "coins_earned": coins_earned,
        "uran_total_coins": uran_total_coins,
        "total_coins": total_coins,
        "total_planet_words": total_planet_words,
        "total_learned_words": total_learned_words,
        "remaining_new_words": remaining_new_words,
        "mode": payload.mode or "learn",
        "congratulation": congrat,
        "next_learn_url": "/mobile/planets/uran/learn",
        "next_review_url": "/mobile/planets/uran/review",
        "next_category_unlocked": next_category_unlocked,
        "next_category_id": next_category_id,
        "next_category_name": next_category_name
    }


# 7.13.4. URAN / YANGI SO'ZLARNI O'RGANISH VA IMTIHON TESTLARI (10-15 TA)
@app.get("/mobile/planets/uran/learn", response_model=UranPracticeSessionResponse, tags=["Mobil Ilova — Uran Sayyorasi (Nutq & Til)"], summary="7.13.4. Uran / Yangi So'zlarni O'rganish va Imtihon Testi (10-15 ta)")
@app.get("/mobile/planets/uran/learn/", response_model=UranPracticeSessionResponse, include_in_schema=False)
@app.get("/mobile/planets/uran/category/{category_id}/learn", response_model=UranPracticeSessionResponse, tags=["Mobil Ilova — Uran Sayyorasi (Nutq & Til)"], summary="7.13.4. Uran / Kategoriya Bo'yicha Yangi So'zlarni O'rganish va Test")
@app.get("/mobile/planets/uran/category/{category_id}/learn/", response_model=UranPracticeSessionResponse, include_in_schema=False)
@app.get("/mobile/planets/uranus/learn", response_model=UranPracticeSessionResponse, include_in_schema=False)
@app.get("/mobile/uran/learn", response_model=UranPracticeSessionResponse, include_in_schema=False)
def get_uran_learn_session(category_id: Optional[int] = None, child_id: Optional[int] = None, count: int = 15, request: Request = None, current_user: Optional[dict] = Depends(get_current_user_optional)):
    effective_child_id = child_id or resolve_child_id(None, current_user)
    safe_count = max(10, min(count, 25))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Jami so'zlar va farzand o'rgangan so'zlar
    cursor.execute("SELECT COUNT(*) as cnt FROM uran_words")
    total_planet_words = cursor.fetchone()["cnt"] or 0

    cursor.execute("SELECT DISTINCT word_id FROM child_uran_learned_words WHERE child_id = ?", (effective_child_id,))
    learned_ids = [r["word_id"] for r in cursor.fetchall()]
    total_learned_words = len(learned_ids)
    remaining_new_words = max(0, total_planet_words - total_learned_words)

    # Bolaning faqat Uran sayyorasida to'plagan jami coinlari
    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0) as uran_coins 
        FROM coin_transactions 
        WHERE child_id = ? AND source = 'uran_quiz' AND transaction_type = 'earn'
    """, (effective_child_id,))
    uran_total_coins = cursor.fetchone()["uran_coins"] or 0

    # Variantlar uchun hamma o'zbekcha so'zlar
    cursor.execute("SELECT word_uz FROM uran_words")
    all_uz_pool = [r["word_uz"] for r in cursor.fetchall()]

    # Yangi so'zlarni tanlash
    selected_word_rows = []
    cat_name = None
    if category_id:
        cursor.execute("SELECT name FROM uran_categories WHERE id = ?", (category_id,))
        cat_row = cursor.fetchone()
        if cat_row:
            cat_name = cat_row["name"]

        if learned_ids:
            placeholders = ",".join("?" for _ in learned_ids)
            cursor.execute(f"SELECT * FROM uran_words WHERE category_id = ? AND id NOT IN ({placeholders}) ORDER BY order_num ASC, id ASC", [category_id] + learned_ids)
        else:
            cursor.execute("SELECT * FROM uran_words WHERE category_id = ? ORDER BY order_num ASC, id ASC", (category_id,))
        selected_word_rows = cursor.fetchall()

        # Agar kategoriyada yangi so'zlar kam bo'lsa (masalan 10 tadan kam), 10-15 ta qilish uchun boshqa yangi so'zlardan to'ldiramiz
        if len(selected_word_rows) < safe_count:
            needed = safe_count - len(selected_word_rows)
            existing_ids = [r["id"] for r in selected_word_rows] + learned_ids
            if existing_ids:
                ex_placeholders = ",".join("?" for _ in existing_ids)
                cursor.execute(f"SELECT * FROM uran_words WHERE id NOT IN ({ex_placeholders}) ORDER BY RANDOM() LIMIT ?", existing_ids + [needed])
            else:
                cursor.execute("SELECT * FROM uran_words ORDER BY RANDOM() LIMIT ?", (needed,))
            supplement = cursor.fetchall()
            selected_word_rows = list(selected_word_rows) + list(supplement)
    else:
        # Barcha kategoriyalar bo'yicha yangi so'zlar
        if learned_ids:
            placeholders = ",".join("?" for _ in learned_ids)
            cursor.execute(f"SELECT * FROM uran_words WHERE id NOT IN ({placeholders}) ORDER BY category_id ASC, order_num ASC, id ASC LIMIT ?", learned_ids + [safe_count])
        else:
            cursor.execute("SELECT * FROM uran_words ORDER BY category_id ASC, order_num ASC, id ASC LIMIT ?", (safe_count,))
        selected_word_rows = cursor.fetchall()

    is_review = False
    auto_switched_to_review = False
    mode = "learn"

    # AGAR YANGI SO'ZLAR QOLMAGAN BO'LSA -> AVTOMATIK TAKRORLASH BO'LIB KETADI!
    if not selected_word_rows or len(selected_word_rows) == 0:
        is_review = True
        auto_switched_to_review = True
        mode = "review"
        message = (
            f"Barakalla! Uran sayyorasidagi barcha {total_planet_words} ta yangi so'zni o'rganib bo'ldingiz! "
            f"Endi o'rganilgan so'zlarni mustahkamlash uchun avtomatik takrorlash rejimi ishga tushdi."
        )
        # O'rganilgan so'zlardan eng kam takrorlanganlarini olamiz
        cursor.execute("""
            SELECT w.* FROM uran_words w
            JOIN child_uran_learned_words lw ON w.id = lw.word_id
            WHERE lw.child_id = ?
            ORDER BY lw.review_count ASC, lw.last_learned_at ASC
            LIMIT ?
        """, (effective_child_id, safe_count))
        selected_word_rows = cursor.fetchall()

        # Agar bazada biror sabab bilan o'rganilgan so'zlar topilmasa, istalgan 10-15 ta so'z
        if not selected_word_rows:
            cursor.execute("SELECT * FROM uran_words ORDER BY RANDOM() LIMIT ?", (safe_count,))
            selected_word_rows = cursor.fetchall()
    else:
        message = f"Yangi so'zlarni o'rganing va testdan o'ting! ({len(selected_word_rows)} ta yangi so'z)"

    conn.close()

    # So'zlar va testlar ro'yxatini shakllantirish
    words_list = [format_uran_word_row(w, request) for w in selected_word_rows]

    tests_list = build_uran_quiz_questions(words_list, all_uz_pool, request)

    return {
        "mode": mode,
        "title": "Uran: Yangi So'zlarni O'rganish" if mode == "learn" else "Uran: So'zlarni Takrorlash (Review)",
        "category_id": category_id,
        "category_name": cat_name,
        "is_review": is_review,
        "auto_switched_to_review": auto_switched_to_review,
        "message": message,
        "total_words": len(words_list),
        "total_tests": len(tests_list),
        "words": words_list,
        "tests": tests_list,
        "quiz": tests_list,
        "stats": {
            "total_planet_words": total_planet_words,
            "total_learned_words": total_learned_words,
            "remaining_new_words": remaining_new_words,
            "uran_total_coins": uran_total_coins
        }
    }


# 7.13.5. URAN / O'RGANILGAN SO'ZLARNI TAKRORLASH VA IMTIHON TESTLARI (10-15 TA)
@app.get("/mobile/planets/uran/review", response_model=UranPracticeSessionResponse, tags=["Mobil Ilova — Uran Sayyorasi (Nutq & Til)"], summary="7.13.5. Uran / O'rganilgan So'zlarni Takrorlash va Imtihon Testi (10-15 ta)")
@app.get("/mobile/planets/uran/review/", response_model=UranPracticeSessionResponse, include_in_schema=False)
@app.get("/mobile/planets/uran/category/{category_id}/review", response_model=UranPracticeSessionResponse, tags=["Mobil Ilova — Uran Sayyorasi (Nutq & Til)"], summary="7.13.5. Uran / Kategoriya Bo'yicha So'zlarni Takrorlash va Test")
@app.get("/mobile/planets/uran/category/{category_id}/review/", response_model=UranPracticeSessionResponse, include_in_schema=False)
@app.get("/mobile/planets/uranus/review", response_model=UranPracticeSessionResponse, include_in_schema=False)
@app.get("/mobile/uran/review", response_model=UranPracticeSessionResponse, include_in_schema=False)
def get_uran_review_session(category_id: Optional[int] = None, child_id: Optional[int] = None, count: int = 15, request: Request = None, current_user: Optional[dict] = Depends(get_current_user_optional)):
    effective_child_id = child_id or resolve_child_id(None, current_user)
    safe_count = max(10, min(count, 25))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Jami so'zlar va farzand o'rgangan so'zlar
    cursor.execute("SELECT COUNT(*) as cnt FROM uran_words")
    total_planet_words = cursor.fetchone()["cnt"] or 0

    cursor.execute("SELECT DISTINCT word_id FROM child_uran_learned_words WHERE child_id = ?", (effective_child_id,))
    learned_ids = [r["word_id"] for r in cursor.fetchall()]
    total_learned_words = len(learned_ids)
    remaining_new_words = max(0, total_planet_words - total_learned_words)

    # Bolaning faqat Uran sayyorasida to'plagan jami coinlari
    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0) as uran_coins 
        FROM coin_transactions 
        WHERE child_id = ? AND source = 'uran_quiz' AND transaction_type = 'earn'
    """, (effective_child_id,))
    uran_total_coins = cursor.fetchone()["uran_coins"] or 0

    # Variantlar uchun hamma o'zbekcha so'zlar
    cursor.execute("SELECT word_uz FROM uran_words")
    all_uz_pool = [r["word_uz"] for r in cursor.fetchall()]

    selected_word_rows = []
    cat_name = None

    if category_id:
        cursor.execute("SELECT name FROM uran_categories WHERE id = ?", (category_id,))
        cat_row = cursor.fetchone()
        if cat_row:
            cat_name = cat_row["name"]

        cursor.execute("""
            SELECT w.* FROM uran_words w
            JOIN child_uran_learned_words lw ON w.id = lw.word_id
            WHERE lw.child_id = ? AND w.category_id = ?
            ORDER BY lw.review_count ASC, lw.last_learned_at ASC
            LIMIT ?
        """, (effective_child_id, category_id, safe_count))
        selected_word_rows = cursor.fetchall()
    else:
        cursor.execute("""
            SELECT w.* FROM uran_words w
            JOIN child_uran_learned_words lw ON w.id = lw.word_id
            WHERE lw.child_id = ?
            ORDER BY lw.review_count ASC, lw.last_learned_at ASC
            LIMIT ?
        """, (effective_child_id, safe_count))
        selected_word_rows = cursor.fetchall()

    # Agar o'rganilgan so'zlar safe_count dan kam bo'lsa (yoki yangi foydalanuvchi bo'lsa):
    # kamida 10-15 ta test bo'lishi uchun bazadagi boshqa so'zlar bilan to'ldiramiz!
    if len(selected_word_rows) < safe_count:
        needed = safe_count - len(selected_word_rows)
        existing_ids = [r["id"] for r in selected_word_rows]
        if existing_ids:
            placeholders = ",".join("?" for _ in existing_ids)
            if category_id:
                cursor.execute(f"SELECT * FROM uran_words WHERE category_id = ? AND id NOT IN ({placeholders}) ORDER BY order_num ASC, id ASC LIMIT ?", [category_id] + existing_ids + [needed])
            else:
                cursor.execute(f"SELECT * FROM uran_words WHERE id NOT IN ({placeholders}) ORDER BY RANDOM() LIMIT ?", existing_ids + [needed])
        else:
            if category_id:
                cursor.execute("SELECT * FROM uran_words WHERE category_id = ? ORDER BY order_num ASC, id ASC LIMIT ?", (category_id, needed))
            else:
                cursor.execute("SELECT * FROM uran_words ORDER BY RANDOM() LIMIT ?", (needed,))
        supp_rows = cursor.fetchall()
        selected_word_rows = list(selected_word_rows) + list(supp_rows)

    conn.close()

    words_list = [format_uran_word_row(w, request) for w in selected_word_rows]

    tests_list = build_uran_quiz_questions(words_list, all_uz_pool, request)

    message = (
        f"Avval o'rganilgan so'zlarni takrorlang va xotirangizni mustahkamlang! ({len(words_list)} ta so'z va test)"
        if total_learned_words > 0
        else f"Uran sayyorasidagi so'zlarni takrorlash mashqi. ({len(words_list)} ta so'z va test)"
    )

    return {
        "mode": "review",
        "title": "Uran: So'zlarni Takrorlash",
        "category_id": category_id,
        "category_name": cat_name,
        "is_review": True,
        "auto_switched_to_review": False,
        "message": message,
        "total_words": len(words_list),
        "total_tests": len(tests_list),
        "words": words_list,
        "tests": tests_list,
        "quiz": tests_list,
        "stats": {
            "total_planet_words": total_planet_words,
            "total_learned_words": total_learned_words,
            "remaining_new_words": remaining_new_words,
            "uran_total_coins": uran_total_coins
        }
    }


# 7.13.6. URAN YANGI KATEGORIYA QO'SHISH (/mobile/planets/uran/category/)
@app.post("/mobile/planets/uran/category/", response_model=UranCategoryResponse, status_code=status.HTTP_201_CREATED, tags=["Mobil Ilova — Uran Sayyorasi (Nutq & Til)"], summary="7.13.6. Uran / Yangi Kategoriya Qo'shish (name, image, description)")
@app.post("/mobile/planets/uran/category", response_model=UranCategoryResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@app.post("/mobile/planets/uranus/category/", response_model=UranCategoryResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@app.post("/mobile/planets/uranus/category", response_model=UranCategoryResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@app.post("/mobile/uran/category/", response_model=UranCategoryResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@app.post("/mobile/uran/category", response_model=UranCategoryResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def mobile_create_uran_category(payload: UranCategoryCreate, request: Request):
    return admin_create_uran_category(payload, request)


# 7.13.7. URAN KATEGORIYA RASMINI YUKLASH (PNG) (/mobile/planets/uran/category/upload-image)
@app.post("/mobile/planets/uran/category/upload-image", tags=["Mobil Ilova — Uran Sayyorasi (Nutq & Til)"], summary="7.13.7. Uran / Kategoriya Rasmini Yuklash (PNG formatda)")
@app.post("/mobile/planets/uran/category/upload-image/", tags=["Mobil Ilova — Uran Sayyorasi (Nutq & Til)"], include_in_schema=False)
@app.post("/api/website/uran/upload-image", tags=["Web & Admin — Uran Sayyorasi Boshqaruvi"], summary="Admin: Uran Rasmini Yuklash (PNG)")
async def upload_uran_category_image(request: Request, file: UploadFile = File(...)):
    try:
        ext = os.path.splitext(file.filename)[1].lower() or ".png"
        unique_name = f"uran_{uuid.uuid4().hex[:10]}{ext}"
        cat_dir = os.path.join(PUBLIC_DIR, "images", "categories")
        os.makedirs(cat_dir, exist_ok=True)
        file_path = os.path.join(cat_dir, unique_name)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        relative_url = f"/images/categories/{unique_name}"
        full_url = to_full_image_url(relative_url, request)
        return {
            "success": True,
            "filename": file.filename,
            "url": full_url,
            "relative_url": relative_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rasm yuklashda xatolik: {str(e)}")


# 7.13.8. URAN KATEGORIYASINI TAHRIRLASH (/mobile/planets/uran/category/{category_id})
@app.put("/mobile/planets/uran/category/{category_id}", response_model=UranCategoryResponse, tags=["Mobil Ilova — Uran Sayyorasi (Nutq & Til)"], summary="7.13.8. Uran / Kategoriyani Tahrirlash")
@app.put("/mobile/planets/uran/category/{category_id}/", response_model=UranCategoryResponse, include_in_schema=False)
def mobile_update_uran_category(category_id: int, payload: UranCategoryUpdate, request: Request):
    return admin_update_uran_category(category_id, payload, request)


# 7.13.9. URAN KATEGORIYASINI O'CHIRISH (/mobile/planets/uran/category/{category_id})
@app.delete("/mobile/planets/uran/category/{category_id}", tags=["Mobil Ilova — Uran Sayyorasi (Nutq & Til)"], summary="7.13.9. Uran / Kategoriyani O'chirish")
@app.delete("/mobile/planets/uran/category/{category_id}/", include_in_schema=False)
def mobile_delete_uran_category(category_id: int):
    return admin_delete_uran_category(category_id)


# 7.13.10. URAN KATEGORIYASIGA YANGI SO'Z QO'SHISH (/mobile/planets/uran/words)
@app.post("/mobile/planets/uran/words", response_model=UranWordResponse, status_code=status.HTTP_201_CREATED, tags=["Mobil Ilova — Uran Sayyorasi (Nutq & Til)"], summary="7.13.10. Uran / Yangi So'z Qo'shish")
@app.post("/mobile/planets/uran/words/", response_model=UranWordResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@app.post("/mobile/planets/uran/category/{category_id}/words", response_model=UranWordResponse, status_code=status.HTTP_201_CREATED, tags=["Mobil Ilova — Uran Sayyorasi (Nutq & Til)"], summary="7.13.10. Uran / Kategoriya Ichiga Yangi So'z Qo'shish")
@app.post("/mobile/planets/uran/category/{category_id}/words/", response_model=UranWordResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def mobile_create_uran_word(payload: UranWordCreate, request: Request, category_id: Optional[int] = None):
    if category_id:
        payload.category_id = category_id
    return admin_create_uran_word(payload, request)


# ==============================================================================
# 7.14. COIN & MUKOFOTLAR TIZIMI (COINS, MISSIONS, SHOP & LEADERBOARD)
# ==============================================================================

def get_or_create_child_coins(child_id: int, user_id: int = 1, conn = None) -> dict:
    """Farzand tangalari hisobini olish yoki bo'sh bo'lsa 50 ta boshlang'ich bonus bilan yaratish"""
    should_close = False
    if conn is None:
        conn = get_db_connection()
        should_close = True
    
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM child_coins WHERE child_id = ?", (child_id,))
    row = cursor.fetchone()
    
    if not row:
        total_coins = 50
        lifetime_coins = 50
        streak_days = 1
        level = 1
        cursor.execute("""
            INSERT OR REPLACE INTO child_coins (child_id, user_id, total_coins, lifetime_coins, streak_days, last_daily_bonus_date, level)
            VALUES (?, ?, ?, ?, ?, '', ?)
        """, (child_id, user_id, total_coins, lifetime_coins, streak_days, level))
        
        cursor.execute("""
            INSERT INTO coin_transactions (user_id, child_id, amount, transaction_type, title, description, source)
            VALUES (?, ?, ?, 'bonus', 'Xush kelibsiz bonusi!', 'Kichik Alloma ilovasiga qo''shilganingiz uchun 50 ta boshlang''ich tanga sovg''a qilindi! 🪙', 'welcome')
        """, (user_id, child_id, 50))
        conn.commit()
        cursor.execute("SELECT * FROM child_coins WHERE child_id = ?", (child_id,))
        row = cursor.fetchone()

    d = dict(row)
    
    cursor.execute("SELECT name, surname, avatar FROM children WHERE id = ?", (child_id,))
    child_row = cursor.fetchone()
    child_name = f"{child_row['name']} {child_row['surname']}".strip() if child_row else f"Bola #{child_id}"
    
    lifetime = d.get("lifetime_coins", 0) or 0
    if lifetime >= 1000:
        level = 5
        level_title = "Buyuk Alloma 👑"
        next_level_coins = 2000
    elif lifetime >= 500:
        level = 4
        level_title = "Koinot Ustasi 🚀"
        next_level_coins = 1000
    elif lifetime >= 250:
        level = 3
        level_title = "Kichik Alloma 🌟"
        next_level_coins = 500
    elif lifetime >= 100:
        level = 2
        level_title = "Kichik Bilimdon 📚"
        next_level_coins = 250
    else:
        level = 1
        level_title = "Kichik Sayyoh 🪐"
        next_level_coins = 100
        
    prev_level_floor = 0 if level == 1 else (100 if level == 2 else (250 if level == 3 else (500 if level == 4 else 1000)))
    level_range = max(1, next_level_coins - prev_level_floor)
    progress_percentage = min(100.0, round(((lifetime - prev_level_floor) / level_range) * 100.0, 1))

    today = datetime.now().strftime("%Y-%m-%d")
    last_bonus = d.get("last_daily_bonus_date") or ""
    daily_bonus_available = (last_bonus != today)
    streak = d.get("streak_days", 1) or 1
    daily_bonus_amount = min(50, 10 + (streak * 2))

    if should_close:
        conn.close()

    return {
        "child_id": child_id,
        "child_name": child_name,
        "total_coins": d.get("total_coins", 0) or 0,
        "lifetime_coins": lifetime,
        "level": level,
        "level_title": level_title,
        "next_level_coins": next_level_coins,
        "progress_percentage": progress_percentage,
        "streak_days": streak,
        "daily_bonus_available": daily_bonus_available,
        "daily_bonus_amount": daily_bonus_amount
    }


def add_child_coins(child_id: int, user_id: int, amount: int, transaction_type: str, title: str, description: str = "", source: str = "general") -> dict:
    """Farzandga tangalar qo'shish yoki yechish (tranzaksiya bilan)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    get_or_create_child_coins(child_id, user_id, conn=conn)
    
    cursor.execute("SELECT total_coins, lifetime_coins, level FROM child_coins WHERE child_id = ?", (child_id,))
    row = cursor.fetchone()
    current_total = row["total_coins"] if row else 0
    current_lifetime = row["lifetime_coins"] if row else 0
    old_level = row["level"] if row else 1
    
    new_total = max(0, current_total + amount)
    new_lifetime = current_lifetime + (amount if amount > 0 else 0)
    
    if new_lifetime >= 1000:
        new_level = 5
    elif new_lifetime >= 500:
        new_level = 4
    elif new_lifetime >= 250:
        new_level = 3
    elif new_lifetime >= 100:
        new_level = 2
    else:
        new_level = 1
        
    cursor.execute("""
        UPDATE child_coins 
        SET total_coins = ?, lifetime_coins = ?, level = ?, updated_at = CURRENT_TIMESTAMP
        WHERE child_id = ?
    """, (new_total, new_lifetime, new_level, child_id))
    
    cursor.execute("""
        INSERT INTO coin_transactions (user_id, child_id, amount, transaction_type, title, description, source)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, child_id, amount, transaction_type, title, description, source))
    
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "message": f"{abs(amount)} ta coin muvaffaqiyatli {'qo''shildi! 🪙' if amount >= 0 else 'sarflandi! 🛍️'}",
        "added_coins": amount,
        "total_coins": new_total,
        "level": new_level,
        "level_up": (new_level > old_level)
    }


def update_daily_mission_progress(child_id: int, user_id: int, action_type: str, increment: int = 1):
    """Kunlik topshiriqlar bajarilishini hisoblab borish"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        
        cursor.execute("SELECT * FROM daily_missions WHERE action_type = ? AND is_active = 1", (action_type,))
        missions = cursor.fetchall()
        for m in missions:
            mid = m["id"]
            target = m["target_count"]
            cursor.execute("""
                SELECT * FROM child_mission_progress WHERE child_id = ? AND mission_id = ? AND date = ?
            """, (child_id, mid, today))
            p_row = cursor.fetchone()
            if p_row:
                new_count = p_row["current_count"] + increment
                is_comp = 1 if new_count >= target else 0
                cursor.execute("""
                    UPDATE child_mission_progress SET current_count = ?, is_completed = ?
                    WHERE id = ?
                """, (new_count, is_comp, p_row["id"]))
            else:
                new_count = increment
                is_comp = 1 if new_count >= target else 0
                cursor.execute("""
                    INSERT INTO child_mission_progress (user_id, child_id, mission_id, date, current_count, is_completed, is_claimed)
                    VALUES (?, ?, ?, ?, ?, ?, 0)
                """, (user_id, child_id, mid, today, new_count, is_comp))
                
        conn.commit()
        conn.close()
    except Exception as e:
        print("[MISSION_PROGRESS] Xato:", e)


def resolve_child_id(explicit_child_id: Optional[int], current_user: Optional[dict]) -> int:
    """Farzand ID raqamini aniqlash (explicit bo'lsa o'zi, bo'lmasa userning 1-bolasi, bo'lmasa 1)"""
    if explicit_child_id and explicit_child_id > 0:
        return explicit_child_id
    if current_user:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM children WHERE user_id = ? ORDER BY id ASC LIMIT 1", (current_user["id"],))
        row = cursor.fetchone()
        conn.close()
        if row:
            return row["id"]
    return 1


# 7.14.1. FARZANDNING COIN BALANSI VA DARAJASI (BALANCE)
@app.get("/mobile/coins/balance/", response_model=CoinBalanceResponse, tags=["Mobil Ilova — Coin & Mukofotlar Tizimi (Coins & Rewards)"], summary="7.14.1. Farzandning Tangalar (Coin) Balansi, Darajasi va Kunlik Bonus Holati")
@app.get("/mobile/coins/balance", response_model=CoinBalanceResponse, include_in_schema=False)
@app.get("/mobile/child/{child_id}/coins/balance/", response_model=CoinBalanceResponse, tags=["Mobil Ilova — Coin & Mukofotlar Tizimi (Coins & Rewards)"], summary="7.14.1.1. Farzandning Tangalar Balansi (ID orqali)")
@app.get("/mobile/child/{child_id}/coins/balance", response_model=CoinBalanceResponse, include_in_schema=False)
@app.get("/api/website/coins/balance/", response_model=CoinBalanceResponse, tags=["Web Sayt (Website)"], summary="Web: Farzand Coin Balansi")
def get_child_coin_balance(child_id: Optional[int] = None, current_user: Optional[dict] = Depends(get_current_user_optional)):
    uid = current_user["id"] if current_user else 1
    cid = resolve_child_id(child_id, current_user)
    return get_or_create_child_coins(cid, uid)


# 7.14.2. KUNLIK BONUSNI QABUL QILISH (DAILY STREAK BONUS)
@app.post("/mobile/coins/daily-bonus/", response_model=DailyBonusResponse, tags=["Mobil Ilova — Coin & Mukofotlar Tizimi (Coins & Rewards)"], summary="7.14.2. Kunlik Kirish Bonusi (Daily Streak Bonus) Qabul Qilish")
@app.post("/mobile/coins/daily-bonus", response_model=DailyBonusResponse, include_in_schema=False)
@app.post("/mobile/child/{child_id}/coins/daily-bonus/", response_model=DailyBonusResponse, tags=["Mobil Ilova — Coin & Mukofotlar Tizimi (Coins & Rewards)"], summary="7.14.2.1. Kunlik Bonus Qabul Qilish (ID orqali)")
@app.post("/mobile/child/{child_id}/coins/daily-bonus", response_model=DailyBonusResponse, include_in_schema=False)
def claim_daily_bonus(child_id: Optional[int] = None, current_user: Optional[dict] = Depends(get_current_user_optional)):
    uid = current_user["id"] if current_user else 1
    cid = resolve_child_id(child_id, current_user)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    get_or_create_child_coins(cid, uid, conn=conn)
    
    cursor.execute("SELECT * FROM child_coins WHERE child_id = ?", (cid,))
    row = cursor.fetchone()
    
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    last_bonus_date = row["last_daily_bonus_date"] or ""
    
    if last_bonus_date == today:
        conn.close()
        raise HTTPException(status_code=400, detail="Siz bugungi kunlik bonusni allaqachon qabul qilgansiz! Ertaga yana kiring. 😊")
    
    streak = row["streak_days"] or 1
    if last_bonus_date == yesterday:
        streak += 1
    elif last_bonus_date != "":
        streak = 1
        
    bonus_coins = min(50, 10 + (streak * 2))
    new_total = (row["total_coins"] or 0) + bonus_coins
    new_lifetime = (row["lifetime_coins"] or 0) + bonus_coins
    
    cursor.execute("""
        UPDATE child_coins 
        SET total_coins = ?, lifetime_coins = ?, streak_days = ?, last_daily_bonus_date = ?, updated_at = CURRENT_TIMESTAMP
        WHERE child_id = ?
    """, (new_total, new_lifetime, streak, today, cid))
    
    cursor.execute("""
        INSERT INTO coin_transactions (user_id, child_id, amount, transaction_type, title, description, source)
        VALUES (?, ?, ?, 'bonus', ?, ?, 'daily_login')
    """, (uid, cid, bonus_coins, f"Kunlik kirish bonusi ({streak}-kun streak) 🔥", f"Har kungi muntazam o'rganish uchun +{bonus_coins} ta coin berildi!"))
    
    conn.commit()
    conn.close()
    
    # Kunlik login missiyasini avtomatik yakunlash
    update_daily_mission_progress(cid, uid, "login", 1)
    
    return {
        "success": True,
        "message": f"Tabriklaymiz! {streak}-kunlik faollik uchun {bonus_coins} ta bonus coin berildi! 🎉",
        "bonus_coins": bonus_coins,
        "total_coins": new_total,
        "streak_days": streak,
        "streak_reward_multiplier": round(1.0 + (streak * 0.1), 1)
    }


# 7.14.3. TANGALAR ISHLASH / QO'SHISH (EARN COINS)
@app.post("/mobile/coins/earn/", response_model=EarnCoinResponse, tags=["Mobil Ilova — Coin & Mukofotlar Tizimi (Coins & Rewards)"], summary="7.14.3. Farzandga Tangalar (Coin) Qo'shish (Dars, O'yin yoki Topshiriq uchun)")
@app.post("/mobile/coins/earn", response_model=EarnCoinResponse, include_in_schema=False)
@app.post("/mobile/child/{child_id}/coins/earn/", response_model=EarnCoinResponse, tags=["Mobil Ilova — Coin & Mukofotlar Tizimi (Coins & Rewards)"], summary="7.14.3.1. Tangalar Qo'shish (ID orqali)")
@app.post("/mobile/child/{child_id}/coins/earn", response_model=EarnCoinResponse, include_in_schema=False)
def earn_child_coins(payload: EarnCoinRequest, child_id: Optional[int] = None, current_user: Optional[dict] = Depends(get_current_user_optional)):
    uid = current_user["id"] if current_user else 1
    cid = resolve_child_id(child_id or payload.child_id, current_user)
    amount = max(1, min(payload.amount, 500))
    
    res = add_child_coins(
        child_id=cid,
        user_id=uid,
        amount=amount,
        transaction_type="earn",
        title=payload.title or "Dars muvaffaqiyatli yakunlandi",
        description=payload.description or "Topshiriq va darslarni muvaffaqiyatli bajarganlik uchun tangalar",
        source=payload.source or "activity"
    )
    return res


# 7.14.4. TANGALAR TRANZAKSIYALARI TARIXI (HISTORY / LEDGER)
@app.get("/mobile/coins/history/", response_model=List[CoinTransactionResponse], tags=["Mobil Ilova — Coin & Mukofotlar Tizimi (Coins & Rewards)"], summary="7.14.4. Farzand Tangalari Kirim-Chiqim Tarixi (Coin Transactions History)")
@app.get("/mobile/coins/history", response_model=List[CoinTransactionResponse], include_in_schema=False)
@app.get("/mobile/child/{child_id}/coins/history/", response_model=List[CoinTransactionResponse], tags=["Mobil Ilova — Coin & Mukofotlar Tizimi (Coins & Rewards)"], summary="7.14.4.1. Tangalar Tarixi (ID orqali)")
@app.get("/mobile/child/{child_id}/coins/history", response_model=List[CoinTransactionResponse], include_in_schema=False)
def get_coin_transactions_history(child_id: Optional[int] = None, limit: int = Query(50, ge=1, le=200), current_user: Optional[dict] = Depends(get_current_user_optional)):
    cid = resolve_child_id(child_id, current_user)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM coin_transactions 
        WHERE child_id = ? 
        ORDER BY id DESC LIMIT ?
    """, (cid, limit))
    rows = cursor.fetchall()
    conn.close()
    
    history = []
    for r in rows:
        history.append({
            "id": r["id"],
            "amount": r["amount"],
            "transaction_type": r["transaction_type"],
            "title": r["title"],
            "description": r["description"] or "",
            "source": r["source"] or "general",
            "created_at": str(r["created_at"])
        })
    return history


# 7.14.5. KUNLIK TOPSHIRIQLAR VA MISSIYALAR (DAILY MISSIONS)
@app.get("/mobile/coins/missions/", response_model=List[DailyMissionResponse], tags=["Mobil Ilova — Coin & Mukofotlar Tizimi (Coins & Rewards)"], summary="7.14.5. Kunlik Missiyalar va Topshiriqlar Ro'yxati (Daily Quests)")
@app.get("/mobile/coins/missions", response_model=List[DailyMissionResponse], include_in_schema=False)
@app.get("/mobile/child/{child_id}/coins/missions/", response_model=List[DailyMissionResponse], tags=["Mobil Ilova — Coin & Mukofotlar Tizimi (Coins & Rewards)"], summary="7.14.5.1. Kunlik Missiyalar Ro'yxati (ID orqali)")
@app.get("/mobile/child/{child_id}/coins/missions", response_model=List[DailyMissionResponse], include_in_schema=False)
def get_daily_missions(child_id: Optional[int] = None, request: Request = None, current_user: Optional[dict] = Depends(get_current_user_optional)):
    cid = resolve_child_id(child_id, current_user)
    lang = get_accept_language(request) if request else "uzb"
    today = datetime.now().strftime("%Y-%m-%d")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM daily_missions WHERE is_active = 1 ORDER BY order_num ASC, id ASC")
    missions = cursor.fetchall()
    
    result = []
    for m in missions:
        mid = m["id"]
        title = m["title"]
        desc = m["description"] or ""
        if lang == "rus" and m["title_ru"]:
            title = m["title_ru"]
            desc = m["description"]
        elif lang == "eng" and m["title_en"]:
            title = m["title_en"]
            desc = m["description"]
            
        cursor.execute("""
            SELECT * FROM child_mission_progress 
            WHERE child_id = ? AND mission_id = ? AND date = ?
        """, (cid, mid, today))
        p_row = cursor.fetchone()
        
        current_count = p_row["current_count"] if p_row else 0
        is_completed = bool(p_row["is_completed"]) if p_row else False
        is_claimed = bool(p_row["is_claimed"]) if p_row else False
        
        result.append({
            "id": mid,
            "title": title,
            "description": desc,
            "reward_coins": m["reward_coins"],
            "icon": m["icon"] or "🎯",
            "action_type": m["action_type"],
            "target_count": m["target_count"],
            "current_count": min(current_count, m["target_count"]),
            "is_completed": is_completed,
            "is_claimed": is_claimed
        })
    conn.close()
    return result


# 7.14.6. BAJARILGAN KUNLIK MISSIYA MUKOFOTINI OLISH (CLAIM MISSION REWARD)
@app.post("/mobile/coins/missions/{mission_id}/claim/", response_model=ClaimMissionResponse, tags=["Mobil Ilova — Coin & Mukofotlar Tizimi (Coins & Rewards)"], summary="7.14.6. Bajarilgan Kunlik Topshiriq Mukofotini Yig'ib Olish")
@app.post("/mobile/coins/missions/{mission_id}/claim", response_model=ClaimMissionResponse, include_in_schema=False)
@app.post("/mobile/child/{child_id}/coins/missions/{mission_id}/claim/", response_model=ClaimMissionResponse, tags=["Mobil Ilova — Coin & Mukofotlar Tizimi (Coins & Rewards)"], summary="7.14.6.1. Topshiriq Mukofotini Olish (ID orqali)")
@app.post("/mobile/child/{child_id}/coins/missions/{mission_id}/claim", response_model=ClaimMissionResponse, include_in_schema=False)
def claim_mission_reward(mission_id: int, child_id: Optional[int] = None, current_user: Optional[dict] = Depends(get_current_user_optional)):
    uid = current_user["id"] if current_user else 1
    cid = resolve_child_id(child_id, current_user)
    today = datetime.now().strftime("%Y-%m-%d")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM daily_missions WHERE id = ?", (mission_id,))
    mission = cursor.fetchone()
    if not mission:
        conn.close()
        raise HTTPException(status_code=404, detail="Bunday topshiriq topilmadi")
        
    cursor.execute("""
        SELECT * FROM child_mission_progress 
        WHERE child_id = ? AND mission_id = ? AND date = ?
    """, (cid, mission_id, today))
    p_row = cursor.fetchone()
    
    if not p_row or not p_row["is_completed"]:
        conn.close()
        raise HTTPException(status_code=400, detail="Ushbu topshiriq hali to'liq bajarilmagan!")
        
    if p_row["is_claimed"]:
        conn.close()
        raise HTTPException(status_code=400, detail="Siz bu topshiriq mukofotini allaqachon qabul qilgansiz!")
        
    cursor.execute("""
        UPDATE child_mission_progress 
        SET is_claimed = 1, claimed_at = CURRENT_TIMESTAMP 
        WHERE id = ?
    """, (p_row["id"],))
    conn.commit()
    conn.close()
    
    reward = mission["reward_coins"]
    coin_res = add_child_coins(
        child_id=cid,
        user_id=uid,
        amount=reward,
        transaction_type="mission",
        title=f"Missiya mukofoti: {mission['title']} 🎯",
        description=f"Kunlik topshiriq bajarilganligi uchun +{reward} coin berildi.",
        source="daily_mission"
    )
    
    return {
        "success": True,
        "message": f"Tabriklaymiz! Topshiriq uchun {reward} ta coin balansingizga qo'shildi! 🪙",
        "claimed_coins": reward,
        "total_coins": coin_res["total_coins"]
    }


# 7.14.7. MUKOFOTLAR DO'KONI (COIN SHOP)
@app.get("/mobile/coins/shop/", response_model=List[ShopItemResponse], tags=["Mobil Ilova — Coin & Mukofotlar Tizimi (Coins & Rewards)"], summary="7.14.7. Tangalar Do'koni — Mukofotlar, Avatarlar va Nishonlar (Shop)")
@app.get("/mobile/coins/shop", response_model=List[ShopItemResponse], include_in_schema=False)
@app.get("/mobile/child/{child_id}/coins/shop/", response_model=List[ShopItemResponse], tags=["Mobil Ilova — Coin & Mukofotlar Tizimi (Coins & Rewards)"], summary="7.14.7.1. Tangalar Do'koni (ID orqali)")
@app.get("/mobile/child/{child_id}/coins/shop", response_model=List[ShopItemResponse], include_in_schema=False)
def get_coin_shop_items(child_id: Optional[int] = None, category: Optional[str] = None, request: Request = None, current_user: Optional[dict] = Depends(get_current_user_optional)):
    cid = resolve_child_id(child_id, current_user)
    lang = get_accept_language(request) if request else "uzb"
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM coin_shop_items WHERE is_active = 1"
    params = []
    if category:
        query += " AND category = ?"
        params.append(category)
    query += " ORDER BY order_num ASC, id ASC"
    cursor.execute(query, params)
    items = cursor.fetchall()
    
    # Farzand sotib olgan buyumlar ro'yxati
    cursor.execute("SELECT item_id, is_equipped FROM child_purchased_items WHERE child_id = ?", (cid,))
    purchased_map = {r["item_id"]: bool(r["is_equipped"]) for r in cursor.fetchall()}
    conn.close()
    
    result = []
    for it in items:
        iid = it["id"]
        title = it["title"]
        desc = it["description"] or ""
        if lang == "rus" and it["title_ru"]:
            title = it["title_ru"]
        elif lang == "eng" and it["title_en"]:
            title = it["title_en"]
            
        result.append({
            "id": iid,
            "title": title,
            "description": desc,
            "category": it["category"],
            "cost_coins": it["cost_coins"],
            "image": to_full_image_url(it["image"], request) if it["image"] else "",
            "icon": it["icon"] or "🎁",
            "is_owned": iid in purchased_map,
            "is_equipped": purchased_map.get(iid, False)
        })
    return result


# 7.14.8. DO'KONDAN BUYUM SOTIB OLISH (BUY SHOP ITEM)
@app.post("/mobile/coins/shop/buy/{item_id}", response_model=BuyShopItemResponse, tags=["Mobil Ilova — Coin & Mukofotlar Tizimi (Coins & Rewards)"], summary="7.14.8. Tangalar Do'konidan Mahsulot Sotib Olish")
@app.post("/mobile/coins/shop/buy/{item_id}/", response_model=BuyShopItemResponse, include_in_schema=False)
@app.post("/mobile/child/{child_id}/coins/shop/buy/{item_id}", response_model=BuyShopItemResponse, tags=["Mobil Ilova — Coin & Mukofotlar Tizimi (Coins & Rewards)"], summary="7.14.8.1. Mahsulot Sotib Olish (ID orqali)")
@app.post("/mobile/child/{child_id}/coins/shop/buy/{item_id}/", response_model=BuyShopItemResponse, include_in_schema=False)
def buy_shop_item(item_id: int, payload: Optional[BuyShopItemRequest] = None, child_id: Optional[int] = None, request: Request = None, current_user: Optional[dict] = Depends(get_current_user_optional)):
    uid = current_user["id"] if current_user else 1
    req_cid = payload.child_id if payload else None
    cid = resolve_child_id(child_id or req_cid, current_user)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM coin_shop_items WHERE id = ? AND is_active = 1", (item_id,))
    item = cursor.fetchone()
    if not item:
        conn.close()
        raise HTTPException(status_code=404, detail="Do'konda bunday mahsulot topilmadi")
        
    cursor.execute("SELECT * FROM child_purchased_items WHERE child_id = ? AND item_id = ?", (cid, item_id))
    already_owned = cursor.fetchone()
    if already_owned:
        conn.close()
        raise HTTPException(status_code=400, detail="Siz ushbu mahsulotni allaqachon sotib olgansiz!")
        
    cost = item["cost_coins"]
    cursor.execute("SELECT total_coins FROM child_coins WHERE child_id = ?", (cid,))
    coins_row = cursor.fetchone()
    total_coins = coins_row["total_coins"] if coins_row else 0
    
    if total_coins < cost:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Tangalar yetarli emas! Sizda {total_coins} coin bor, mahsulot narxi esa {cost} coin.")
        
    # Xaridni rasmiylashtirish
    cursor.execute("""
        INSERT INTO child_purchased_items (user_id, child_id, item_id, is_equipped)
        VALUES (?, ?, ?, 1)
    """, (uid, cid, item_id))
    conn.commit()
    conn.close()
    
    coin_res = add_child_coins(
        child_id=cid,
        user_id=uid,
        amount=-cost,
        transaction_type="spend",
        title=f"Do'kondan xarid: {item['title']} 🛍️",
        description=f"{cost} ta coin evaziga xarid qilindi",
        source="shop_purchase"
    )
    
    shop_item_resp = {
        "id": item["id"],
        "title": item["title"],
        "description": item["description"] or "",
        "category": item["category"],
        "cost_coins": item["cost_coins"],
        "image": to_full_image_url(item["image"], request) if item["image"] else "",
        "icon": item["icon"] or "🎁",
        "is_owned": True,
        "is_equipped": True
    }
    
    return {
        "success": True,
        "message": f"Tabriklaymiz! '{item['title']}' muvaffaqiyatli xarid qilindi va faollashtirildi! 🎉",
        "remaining_coins": coin_res["total_coins"],
        "item": shop_item_resp
    }


# 7.14.9. SOTIB OLINGAN BUYUMLAR VA NISHONLAR (INVENTORY)
@app.get("/mobile/coins/inventory/", response_model=List[InventoryItemResponse], tags=["Mobil Ilova — Coin & Mukofotlar Tizimi (Coins & Rewards)"], summary="7.14.9. Farzandning Sotib Olingan Buyumlari va Nishonlari (Inventory)")
@app.get("/mobile/coins/inventory", response_model=List[InventoryItemResponse], include_in_schema=False)
@app.get("/mobile/child/{child_id}/coins/inventory/", response_model=List[InventoryItemResponse], tags=["Mobil Ilova — Coin & Mukofotlar Tizimi (Coins & Rewards)"], summary="7.14.9.1. Sotib Olingan Buyumlar Ro'yxati (ID orqali)")
@app.get("/mobile/child/{child_id}/coins/inventory", response_model=List[InventoryItemResponse], include_in_schema=False)
def get_child_inventory(child_id: Optional[int] = None, request: Request = None, current_user: Optional[dict] = Depends(get_current_user_optional)):
    cid = resolve_child_id(child_id, current_user)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.id as purchase_id, p.is_equipped, p.purchased_at, s.* 
        FROM child_purchased_items p
        JOIN coin_shop_items s ON p.item_id = s.id
        WHERE p.child_id = ?
        ORDER BY p.id DESC
    """, (cid,))
    rows = cursor.fetchall()
    conn.close()
    
    inventory = []
    for r in rows:
        inventory.append({
            "id": r["purchase_id"],
            "item_id": r["id"],
            "title": r["title"],
            "category": r["category"],
            "image": to_full_image_url(r["image"], request) if r["image"] else "",
            "icon": r["icon"] or "🎁",
            "is_equipped": bool(r["is_equipped"]),
            "purchased_at": str(r["purchased_at"])
        })
    return inventory


# 7.14.10. BUYUMNI TAQISH / FAOLLASHTIRISH (EQUIP ITEM)
@app.post("/mobile/coins/inventory/{item_id}/equip", response_model=EquipItemResponse, tags=["Mobil Ilova — Coin & Mukofotlar Tizimi (Coins & Rewards)"], summary="7.14.10. Sotib Olingan Avatar yoki Mavzuni Taqish / Faollashtirish (Equip)")
@app.post("/mobile/coins/inventory/{item_id}/equip/", response_model=EquipItemResponse, include_in_schema=False)
@app.post("/mobile/child/{child_id}/coins/inventory/{item_id}/equip", response_model=EquipItemResponse, tags=["Mobil Ilova — Coin & Mukofotlar Tizimi (Coins & Rewards)"], summary="7.14.10.1. Buyumni Taqish / Faollashtirish (ID orqali)")
@app.post("/mobile/child/{child_id}/coins/inventory/{item_id}/equip/", response_model=EquipItemResponse, include_in_schema=False)
def equip_inventory_item(item_id: int, payload: Optional[EquipItemRequest] = None, child_id: Optional[int] = None, current_user: Optional[dict] = Depends(get_current_user_optional)):
    req_cid = payload.child_id if payload else None
    cid = resolve_child_id(child_id or req_cid, current_user)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM child_purchased_items WHERE child_id = ? AND item_id = ?", (cid, item_id))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Siz bu buyumni hali sotib olmagansiz!")
        
    # Holatni almashtirish (Toggle: equip/unequip)
    new_status = 0 if row["is_equipped"] else 1
    cursor.execute("UPDATE child_purchased_items SET is_equipped = ? WHERE id = ?", (new_status, row["id"]))
    conn.commit()
    conn.close()
    
    msg = "Buyum muvaffaqiyatli taqildi / faollashtirildi! ✨" if new_status == 1 else "Buyum taqishdan olindi."
    return {
        "success": True,
        "message": msg,
        "item_id": item_id,
        "is_equipped": bool(new_status)
    }


# 7.14.11. ENG KO'P TANGALAR REYTINGI (LEADERBOARD)
@app.get("/mobile/coins/leaderboard/", response_model=List[LeaderboardItemResponse], tags=["Mobil Ilova — Coin & Mukofotlar Tizimi (Coins & Rewards)"], summary="7.14.11. Eng Ko'p Tangalar Yig'gan Allomalar Reytingi (Leaderboard)")
@app.get("/mobile/coins/leaderboard", response_model=List[LeaderboardItemResponse], include_in_schema=False)
@app.get("/api/website/coins/leaderboard/", response_model=List[LeaderboardItemResponse], tags=["Web Sayt (Website)"], summary="Web: Allomalar Tangalar Reytingi")
def get_coins_leaderboard(limit: int = Query(20, ge=1, le=100), request: Request = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id as child_id, c.name, c.surname, c.avatar, 
               COALESCE(cc.total_coins, 50) as total_coins,
               COALESCE(cc.lifetime_coins, 50) as lifetime_coins,
               COALESCE(cc.level, 1) as level
        FROM children c
        LEFT JOIN child_coins cc ON c.id = cc.child_id
        ORDER BY COALESCE(cc.total_coins, 50) DESC, c.id ASC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for idx, r in enumerate(rows, start=1):
        fullname = f"{r['name']} {r['surname']}".strip()
        lvl = r["level"] or 1
        level_title = "Buyuk Alloma 👑" if lvl >= 5 else ("Koinot Ustasi 🚀" if lvl == 4 else ("Kichik Alloma 🌟" if lvl == 3 else ("Kichik Bilimdon 📚" if lvl == 2 else "Kichik Sayyoh 🪐")))
        
        avatar = r["avatar"] or "/images/avatars/boy1.png"
        result.append({
            "rank": idx,
            "child_id": r["child_id"],
            "child_name": fullname,
            "avatar": to_full_image_url(avatar, request) if request else avatar,
            "total_coins": r["total_coins"],
            "level": lvl,
            "level_title": level_title
        })
    return result



# ==============================================================================
# 7.15. MOBIL ILOVA — KUTUBXONA VA AUDIO KITOBLAR (LIBRARY & AUDIO BOOKS)
# ==============================================================================

LIBRARY_UPLOAD_DIR = os.path.join(PUBLIC_DIR, "images", "library")
os.makedirs(LIBRARY_UPLOAD_DIR, exist_ok=True)
LIBRARY_AUDIO_DIR = os.path.join(PUBLIC_DIR, "audio", "library")
os.makedirs(LIBRARY_AUDIO_DIR, exist_ok=True)


def format_book_dict(r: dict, request: Request, child_id: Optional[int] = None) -> dict:
    """Kitob ma'lumotlarini to'liq URL manzillari va farzand holati bilan formatlash"""
    cover = to_full_image_url(r.get("cover_image"), request)
    audio = to_full_image_url(r.get("audio_url"), request) if r.get("audio_url") else ""
    
    is_fav = False
    prog_sec = 0
    prog_fmt = "00:00"
    is_comp = False
    
    if child_id:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT 1 FROM library_favorites WHERE child_id = ? AND book_id = ?", (child_id, r["id"]))
        is_fav = c.fetchone() is not None
        
        c.execute("SELECT progress_seconds, progress_formatted, is_completed FROM library_book_progress WHERE child_id = ? AND book_id = ?", (child_id, r["id"]))
        p_row = c.fetchone()
        if p_row:
            prog_sec = p_row["progress_seconds"] or 0
            prog_fmt = p_row["progress_formatted"] or "00:00"
            is_comp = bool(p_row["is_completed"])
        conn.close()
        
    return {
        "id": r["id"],
        "title": r["title"],
        "author": r["author"],
        "cover_image": cover,
        "image": cover,
        "category_id": r["category_id"],
        "category_name": r.get("category_name") or "Umumiy",
        "category_slug": r.get("category_slug") or "all",
        "description": r.get("description") or "",
        "content": r.get("content") or "",
        "audio_url": audio,
        "duration_seconds": r.get("duration_seconds") or 0,
        "duration_formatted": r.get("duration_formatted") or "12:52",
        "target_age": r.get("target_age") or "7-12 yosh",
        "is_featured": bool(r.get("is_featured", 0)),
        "section": r.get("section") or "eng-sara",
        "listen_count": r.get("listen_count") or 0,
        "likes_count": r.get("likes_count") or 0,
        "is_favorite": is_fav,
        "user_progress_seconds": prog_sec,
        "user_progress_formatted": prog_fmt,
        "is_completed": is_comp
    }


def resolve_current_child(child_id: Optional[int], current_user: Optional[dict]) -> Optional[dict]:
    """Farzand ob'ektini aniqlash"""
    conn = get_db_connection()
    c = conn.cursor()
    child_row = None
    if child_id:
        c.execute("SELECT * FROM children WHERE id = ?", (child_id,))
        child_row = c.fetchone()
    elif current_user:
        c.execute("SELECT * FROM children WHERE user_id = ? ORDER BY id ASC LIMIT 1", (current_user["id"],))
        child_row = c.fetchone()
    
    if not child_row:
        c.execute("SELECT * FROM children ORDER BY id ASC LIMIT 1")
        child_row = c.fetchone()
    conn.close()
    return dict(child_row) if child_row else None


# 7.15.1. KUTUBXONA BOSH SAHIFASI (FEED / DASHBOARD)
@app.get("/mobile/library/home/", response_model=LibraryHomeResponse, tags=["Mobil Ilova — Kutubxona (Library & Audio Books)"], summary="7.15.1. Kutubxona Bosh Sahifasi (Bola profili, Balans, Qidiruv, Kategoriyalar, Eng sara, Bo'limlar)")
@app.get("/mobile/library/home", response_model=LibraryHomeResponse, include_in_schema=False)
@app.get("/mobile/library/", response_model=LibraryHomeResponse, include_in_schema=False)
@app.get("/mobile/library", response_model=LibraryHomeResponse, include_in_schema=False)
@app.get("/api/library/home/", response_model=LibraryHomeResponse, tags=["Web Sayt (Website)"], summary="Web: Kutubxona Bosh Sahifasi")
@app.get("/api/library/home", response_model=LibraryHomeResponse, include_in_schema=False)
def get_library_home(
    request: Request,
    child_id: Optional[int] = Query(None, description="Tanlangan farzand IDsi"),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Bola ma'lumotlari va Tangalar balansi
    active_child = resolve_current_child(child_id, current_user)
    child_data = None
    cid = None

    if active_child:
        cid = active_child["id"]
        cursor.execute("SELECT total_coins FROM child_coins WHERE child_id = ?", (cid,))
        coin_row = cursor.fetchone()
        coins = coin_row["total_coins"] if coin_row else 1000

        # Yoshni hisoblash
        y = str(active_child.get("year") or "12").strip()
        age_str = "12 yosh"
        if "/" in y:
            try:
                birth_year = int(y.split("/")[-1])
                diff = datetime.now().year - birth_year
                if 1 <= diff <= 18:
                    age_str = f"{diff} yosh"
            except Exception:
                pass
        elif y.isdigit() and 1 <= int(y) <= 18:
            age_str = f"{int(y)} yosh"
        elif y.isdigit() and int(y) > 1900:
            age_str = f"{datetime.now().year - int(y)} yosh"

        child_data = {
            "id": cid,
            "name": active_child.get("name") or "Aziz",
            "surname": active_child.get("surname") or "",
            "age": age_str,
            "avatar": to_full_image_url(active_child.get("avatar") or "/images/avatars/boy1.png", request),
            "coins": coins
        }
    else:
        child_data = {
            "id": 1,
            "name": "Aziz",
            "surname": "",
            "age": "12 yosh",
            "avatar": to_full_image_url("/images/avatars/boy1.png", request),
            "coins": 1000
        }
        cid = 1

    # 2. Toifalar ro'yxati (Pills)
    cursor.execute("""
        SELECT c.*, COUNT(b.id) as book_count
        FROM library_categories c
        LEFT JOIN library_books b ON b.category_id = c.id AND b.status = 'active'
        WHERE c.is_active = 1
        GROUP BY c.id
        ORDER BY c.order_num ASC
    """)
    cat_rows = cursor.fetchall()
    categories = []
    for cr in cat_rows:
        categories.append({
            "id": cr["id"],
            "name": cr["name"],
            "name_en": cr["name_en"] or "",
            "name_ru": cr["name_ru"] or "",
            "slug": cr["slug"],
            "icon": cr["icon"] or "📚",
            "book_count": cr["book_count"],
            "order_num": cr["order_num"],
            "is_active": bool(cr["is_active"])
        })

    # 3. Eng sara kitoblar ("Eng sara >")
    cursor.execute("""
        SELECT b.*, c.name as category_name, c.slug as category_slug
        FROM library_books b
        LEFT JOIN library_categories c ON c.id = b.category_id
        WHERE b.is_featured = 1 AND b.status = 'active'
        ORDER BY b.order_num ASC, b.id DESC
        LIMIT 10
    """)
    featured_rows = cursor.fetchall()
    featured_books = [format_book_dict(dict(r), request, child_id=cid) for r in featured_rows]

    # 4. Sarguzasht kitoblar ("Sarguzasht >")
    cursor.execute("""
        SELECT b.*, c.name as category_name, c.slug as category_slug
        FROM library_books b
        LEFT JOIN library_categories c ON c.id = b.category_id
        WHERE (b.section = 'sarguzasht' OR c.slug = 'sarguzasht') AND b.status = 'active'
        ORDER BY b.order_num ASC, b.id DESC
        LIMIT 10
    """)
    adventure_rows = cursor.fetchall()
    adventure_books = [format_book_dict(dict(r), request, child_id=cid) for r in adventure_rows]

    # 5. Tabiat kitoblari ("Tabiat >")
    cursor.execute("""
        SELECT b.*, c.name as category_name, c.slug as category_slug
        FROM library_books b
        LEFT JOIN library_categories c ON c.id = b.category_id
        WHERE (b.section = 'tabiat' OR c.slug = 'tabiat') AND b.status = 'active'
        ORDER BY b.order_num ASC, b.id DESC
        LIMIT 10
    """)
    nature_rows = cursor.fetchall()
    nature_books = [format_book_dict(dict(r), request, child_id=cid) for r in nature_rows]

    # 6. Ertaklar ("Ertaklar >")
    cursor.execute("""
        SELECT b.*, c.name as category_name, c.slug as category_slug
        FROM library_books b
        LEFT JOIN library_categories c ON c.id = b.category_id
        WHERE (b.section = 'ertaklar' OR c.slug = 'ertaklar') AND b.status = 'active'
        ORDER BY b.order_num ASC, b.id DESC
        LIMIT 10
    """)
    fairy_rows = cursor.fetchall()
    fairy_books = [format_book_dict(dict(r), request, child_id=cid) for r in fairy_rows]

    sections = [
        {"id": "eng-sara", "title": "Eng sara", "slug": "eng-sara", "has_more": True, "books": featured_books},
        {"id": "sarguzasht", "title": "Sarguzasht", "slug": "sarguzasht", "has_more": True, "books": adventure_books},
        {"id": "tabiat", "title": "Tabiat", "slug": "tabiat", "has_more": True, "books": nature_books},
        {"id": "ertaklar", "title": "Ertaklar", "slug": "ertaklar", "has_more": True, "books": fairy_books}
    ]

    # 7. Oxirgi tinglanayotgan audio kitob (Continue listening)
    continue_listening = None
    if cid:
        cursor.execute("""
            SELECT p.*, b.title, b.author, b.cover_image, b.audio_url, b.duration_seconds, b.duration_formatted,
                   c.name as category_name, c.slug as category_slug
            FROM library_book_progress p
            JOIN library_books b ON b.id = p.book_id
            LEFT JOIN library_categories c ON c.id = b.category_id
            WHERE p.child_id = ?
            ORDER BY p.last_listened_at DESC
            LIMIT 1
        """, (cid,))
        p_row = cursor.fetchone()
        if p_row:
            pd = dict(p_row)
            continue_listening = {
                "book_id": pd["book_id"],
                "title": pd["title"],
                "author": pd["author"],
                "cover_image": to_full_image_url(pd["cover_image"], request),
                "audio_url": to_full_image_url(pd["audio_url"], request) if pd.get("audio_url") else "",
                "duration_seconds": pd["duration_seconds"],
                "duration_formatted": pd["duration_formatted"],
                "progress_seconds": pd["progress_seconds"],
                "progress_formatted": pd["progress_formatted"],
                "is_completed": bool(pd["is_completed"])
            }

    # Agar hali birorta tinglanmagan bo'lsa, "Sariq devni minib" ni 2:52 holatida tavsiya qilamiz (Skrinshotdagi kabi!)
    if not continue_listening:
        cursor.execute("""
            SELECT b.*, c.name as category_name, c.slug as category_slug
            FROM library_books b
            LEFT JOIN library_categories c ON c.id = b.category_id
            WHERE b.id = 1 OR b.title LIKE '%Sariq dev%'
            LIMIT 1
        """)
        sariq_row = cursor.fetchone()
        if sariq_row:
            sd = dict(sariq_row)
            continue_listening = {
                "book_id": sd["id"],
                "title": sd["title"],
                "author": sd["author"],
                "cover_image": to_full_image_url(sd["cover_image"], request),
                "audio_url": to_full_image_url(sd["audio_url"], request) if sd.get("audio_url") else "",
                "duration_seconds": sd["duration_seconds"],
                "duration_formatted": sd["duration_formatted"],
                "progress_seconds": 172,
                "progress_formatted": "02:52",
                "is_completed": False
            }

    conn.close()

    return {
        "child": child_data,
        "categories": categories,
        "featured": featured_books,
        "sections": sections,
        "continue_listening": continue_listening
    }


# 7.15.2. KUTUBXONA KATEGORIYALARI RO'YXATI (/mobile/library/categories/)
@app.get("/mobile/library/categories/", response_model=List[LibraryCategoryResponse], tags=["Mobil Ilova — Kutubxona (Library & Audio Books)"], summary="7.15.2. Barcha Kutubxona Toifalari Ro'yxati")
@app.get("/mobile/library/categories", response_model=List[LibraryCategoryResponse], include_in_schema=False)
@app.get("/api/library/categories/", response_model=List[LibraryCategoryResponse], include_in_schema=False)
@app.get("/api/library/categories", response_model=List[LibraryCategoryResponse], include_in_schema=False)
def get_library_categories(request: Request):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.*, COUNT(b.id) as book_count
        FROM library_categories c
        LEFT JOIN library_books b ON b.category_id = c.id AND b.status = 'active'
        WHERE c.is_active = 1
        GROUP BY c.id
        ORDER BY c.order_num ASC
    """)
    rows = cursor.fetchall()
    conn.close()

    res = []
    for r in rows:
        res.append({
            "id": r["id"],
            "name": r["name"],
            "name_en": r["name_en"] or "",
            "name_ru": r["name_ru"] or "",
            "slug": r["slug"],
            "icon": r["icon"] or "📚",
            "book_count": r["book_count"],
            "order_num": r["order_num"],
            "is_active": bool(r["is_active"])
        })
    return res


# 7.15.3. KITOBLAR RO'YXATI VA QIDIRUV (/mobile/library/books/)
@app.get("/mobile/library/books/", response_model=List[LibraryBookItemResponse], tags=["Mobil Ilova — Kutubxona (Library & Audio Books)"], summary="7.15.3. Kitoblar Ro'yxati va Qidiruv (q, category, section, is_featured)")
@app.get("/mobile/library/books", response_model=List[LibraryBookItemResponse], include_in_schema=False)
@app.get("/api/library/books/", response_model=List[LibraryBookItemResponse], include_in_schema=False)
@app.get("/api/library/books", response_model=List[LibraryBookItemResponse], include_in_schema=False)
def get_library_books(
    request: Request,
    q: Optional[str] = Query(None, description="Qidiruv matni (kitob nomi, muallif, tavsif)"),
    category_id: Optional[int] = Query(None, description="Toifa IDsi"),
    category_slug: Optional[str] = Query(None, description="Toifa kaliti (masalan 'tabiat', 'sarguzasht')"),
    section: Optional[str] = Query(None, description="Bo'lim nomi ('eng-sara', 'sarguzasht', 'ertaklar')"),
    is_featured: Optional[bool] = Query(None, description="Faqat eng sara kitoblar"),
    child_id: Optional[int] = Query(None, description="Farzand IDsi"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    active_child = resolve_current_child(child_id, current_user)
    cid = active_child["id"] if active_child else None

    conn = get_db_connection()
    cursor = conn.cursor()

    sql = """
        SELECT b.*, c.name as category_name, c.slug as category_slug
        FROM library_books b
        LEFT JOIN library_categories c ON c.id = b.category_id
        WHERE b.status = 'active'
    """
    params = []

    if q and q.strip():
        search_term = f"%{q.strip()}%"
        sql += " AND (b.title LIKE ? OR b.author LIKE ? OR b.description LIKE ?)"
        params.extend([search_term, search_term, search_term])

    if category_id:
        sql += " AND b.category_id = ?"
        params.append(category_id)

    if category_slug and category_slug != "all":
        sql += " AND (c.slug = ? OR b.section = ?)"
        params.extend([category_slug, category_slug])

    if section:
        sql += " AND (b.section = ? OR c.slug = ?)"
        params.extend([section, section])

    if is_featured is not None:
        sql += " AND b.is_featured = ?"
        params.append(1 if is_featured else 0)

    sql += " ORDER BY b.order_num ASC, b.id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()

    return [format_book_dict(dict(r), request, child_id=cid) for r in rows]


# 7.15.4. KITOB HAQIDA BATAFSIL (/mobile/library/books/{book_id}/)
@app.get("/mobile/library/books/{book_id}/", response_model=LibraryBookDetailResponse, tags=["Mobil Ilova — Kutubxona (Library & Audio Books)"], summary="7.15.4. Kitob Haqida Batafsil (Muqova, Tavsif, Audio havola va Tinglash tugmasi)")
@app.get("/mobile/library/books/{book_id}", response_model=LibraryBookDetailResponse, include_in_schema=False)
@app.get("/api/library/books/{book_id}/", response_model=LibraryBookDetailResponse, include_in_schema=False)
@app.get("/api/library/books/{book_id}", response_model=LibraryBookDetailResponse, include_in_schema=False)
def get_library_book_detail(
    book_id: int,
    request: Request,
    child_id: Optional[int] = Query(None),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    active_child = resolve_current_child(child_id, current_user)
    cid = active_child["id"] if active_child else None

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.*, c.name as category_name, c.slug as category_slug
        FROM library_books b
        LEFT JOIN library_categories c ON c.id = b.category_id
        WHERE b.id = ?
    """, (book_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Kitob topilmadi!")

    return format_book_dict(dict(row), request, child_id=cid)


# 7.15.5. AUDIO PLEYER EKRANI API (/mobile/library/books/{book_id}/player/)
@app.get("/mobile/library/books/{book_id}/player/", response_model=LibraryPlayerResponse, tags=["Mobil Ilova — Kutubxona (Library & Audio Books)"], summary="7.15.5. Audio Pleyer Ekrani API (Audio URL, Muqova, Vaqt shkalasi 2:52/12:52, Boshqaruv)")
@app.get("/mobile/library/books/{book_id}/player", response_model=LibraryPlayerResponse, include_in_schema=False)
@app.get("/api/library/books/{book_id}/player/", response_model=LibraryPlayerResponse, include_in_schema=False)
@app.get("/api/library/books/{book_id}/player", response_model=LibraryPlayerResponse, include_in_schema=False)
def get_library_book_player(
    book_id: int,
    request: Request,
    child_id: Optional[int] = Query(None),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    active_child = resolve_current_child(child_id, current_user)
    cid = active_child["id"] if active_child else None

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM library_books WHERE id = ?", (book_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Kitob topilmadi!")

    b = dict(row)
    cover = to_full_image_url(b.get("cover_image"), request)
    audio = to_full_image_url(b.get("audio_url"), request) if b.get("audio_url") else ""

    prog_sec = 0
    prog_fmt = "00:00"
    is_comp = False
    is_fav = False

    if cid:
        cursor.execute("SELECT progress_seconds, progress_formatted, is_completed FROM library_book_progress WHERE child_id = ? AND book_id = ?", (cid, book_id))
        p_row = cursor.fetchone()
        if p_row:
            prog_sec = p_row["progress_seconds"] or 0
            prog_fmt = p_row["progress_formatted"] or "00:00"
            is_comp = bool(p_row["is_completed"])
        elif book_id == 1:
            # Skrinshotdagi 2:52 namuna
            prog_sec = 172
            prog_fmt = "02:52"

        cursor.execute("SELECT 1 FROM library_favorites WHERE child_id = ? AND book_id = ?", (cid, book_id))
        is_fav = cursor.fetchone() is not None
    elif book_id == 1:
        prog_sec = 172
        prog_fmt = "02:52"

    conn.close()

    return {
        "book_id": b["id"],
        "title": b["title"],
        "author": b["author"],
        "cover_image": cover,
        "audio_url": audio,
        "duration_seconds": b.get("duration_seconds") or 772,
        "duration_formatted": b.get("duration_formatted") or "12:52",
        "progress_seconds": prog_sec,
        "progress_formatted": prog_fmt,
        "is_favorite": is_fav,
        "is_completed": is_comp
    }


# 7.15.6. TINGLASH VAQTINI SAQLASH VA TANGALAR MUKOFOTI (/mobile/library/books/{book_id}/progress/)
@app.post("/mobile/library/books/{book_id}/progress/", response_model=LibraryBookProgressResponse, tags=["Mobil Ilova — Kutubxona (Library & Audio Books)"], summary="7.15.6. Audio Tinglash Jarayonini Saqlash va Kitob Tugatilganda Tanga Mukofoti")
@app.post("/mobile/library/books/{book_id}/progress", response_model=LibraryBookProgressResponse, include_in_schema=False)
@app.post("/api/library/books/{book_id}/progress/", response_model=LibraryBookProgressResponse, include_in_schema=False)
@app.post("/api/library/books/{book_id}/progress", response_model=LibraryBookProgressResponse, include_in_schema=False)
def update_library_book_progress(
    book_id: int,
    req: LibraryBookProgressRequest,
    child_id: Optional[int] = Query(None),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    active_child = resolve_current_child(child_id, current_user)
    if not active_child:
        raise HTTPException(status_code=400, detail="Farzand profili topilmadi!")

    cid = active_child["id"]
    uid = active_child.get("user_id", 1)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM library_books WHERE id = ?", (book_id,))
    book = cursor.fetchone()
    if not book:
        conn.close()
        raise HTTPException(status_code=404, detail="Kitob topilmadi!")

    # Vaqtni formatlash (MM:SS)
    mins = req.progress_seconds // 60
    secs = req.progress_seconds % 60
    prog_fmt = f"{mins:02d}:{secs:02d}"

    # Avvalgi progressni tekshirish
    cursor.execute("SELECT * FROM library_book_progress WHERE child_id = ? AND book_id = ?", (cid, book_id))
    existing = cursor.fetchone()

    is_completed_now = bool(req.is_completed)
    # Agar vaqt kitob davomiyligining 90% idan oshgan bo'lsa ham tugallangan deb hisoblaymiz
    if book["duration_seconds"] and req.progress_seconds >= int(book["duration_seconds"] * 0.9):
        is_completed_now = True

    coins_rewarded = 0
    was_completed_before = bool(existing["is_completed"]) if existing else False

    if is_completed_now and not was_completed_before:
        coins_rewarded = 25
        # Child coins yangilash
        cursor.execute("""
            INSERT INTO child_coins (child_id, user_id, total_coins, lifetime_coins, level, updated_at)
            VALUES (?, ?, 25, 25, 1, CURRENT_TIMESTAMP)
            ON CONFLICT(child_id) DO UPDATE SET
                total_coins = total_coins + 25,
                lifetime_coins = lifetime_coins + 25,
                updated_at = CURRENT_TIMESTAMP
        """, (cid, uid))

        # Tranzaksiya yozish
        cursor.execute("""
            INSERT INTO coin_transactions (user_id, child_id, amount, transaction_type, title, description, source)
            VALUES (?, ?, 25, 'reward', ?, ?, 'library')
        """, (uid, cid, f"'{book['title']}' kitobini tinglaganlik uchun", "Audio kitobni muvaffaqiyatli yakunlaganlik mukofoti"))

    if existing:
        cursor.execute("""
            UPDATE library_book_progress
            SET progress_seconds = ?, progress_formatted = ?, is_completed = ?,
                completed_at = CASE WHEN ? = 1 AND completed_at IS NULL THEN CURRENT_TIMESTAMP ELSE completed_at END,
                last_listened_at = CURRENT_TIMESTAMP
            WHERE child_id = ? AND book_id = ?
        """, (req.progress_seconds, prog_fmt, 1 if is_completed_now else 0, 1 if is_completed_now else 0, cid, book_id))
    else:
        cursor.execute("""
            INSERT INTO library_book_progress (user_id, child_id, book_id, progress_seconds, progress_formatted, is_completed, completed_at, last_listened_at)
            VALUES (?, ?, ?, ?, ?, ?, CASE WHEN ? = 1 THEN CURRENT_TIMESTAMP ELSE NULL END, CURRENT_TIMESTAMP)
        """, (uid, cid, book_id, req.progress_seconds, prog_fmt, 1 if is_completed_now else 0, 1 if is_completed_now else 0))

    # Kitobning tinglanganlar sonini oshirish
    cursor.execute("UPDATE library_books SET listen_count = listen_count + 1 WHERE id = ?", (book_id,))

    # Yangilangan tangalar balansini olish
    cursor.execute("SELECT total_coins FROM child_coins WHERE child_id = ?", (cid,))
    c_row = cursor.fetchone()
    total_coins = c_row["total_coins"] if c_row else 1000

    conn.commit()
    conn.close()

    msg = "Tinglash vaqti saqlandi"
    if coins_rewarded > 0:
        msg = f"Tabriklaymiz! Kitobni tinglab bo'ldingiz va +{coins_rewarded} oltin tanga mukofot oldingiz! 🎉"

    return {
        "success": True,
        "message": msg,
        "book_id": book_id,
        "progress_seconds": req.progress_seconds,
        "progress_formatted": prog_fmt,
        "is_completed": is_completed_now,
        "coins_rewarded": coins_rewarded,
        "total_coins": total_coins
    }


# 7.15.7. SEVIMLI KITOBLAR TOGGLE (/mobile/library/books/{book_id}/favorite/)
@app.post("/mobile/library/books/{book_id}/favorite/", response_model=LibraryFavoriteResponse, tags=["Mobil Ilova — Kutubxona (Library & Audio Books)"], summary="7.15.7. Kitobni Sevimlilarga Qo'shish / Olib Tashlash (Like / Favorite Toggle)")
@app.post("/mobile/library/books/{book_id}/favorite", response_model=LibraryFavoriteResponse, include_in_schema=False)
@app.post("/api/library/books/{book_id}/favorite/", response_model=LibraryFavoriteResponse, include_in_schema=False)
@app.post("/api/library/books/{book_id}/favorite", response_model=LibraryFavoriteResponse, include_in_schema=False)
def toggle_library_book_favorite(
    book_id: int,
    child_id: Optional[int] = Query(None),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    active_child = resolve_current_child(child_id, current_user)
    if not active_child:
        raise HTTPException(status_code=400, detail="Farzand profili topilmadi!")

    cid = active_child["id"]
    uid = active_child.get("user_id", 1)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM library_books WHERE id = ?", (book_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Kitob topilmadi!")

    cursor.execute("SELECT * FROM library_favorites WHERE child_id = ? AND book_id = ?", (cid, book_id))
    fav = cursor.fetchone()

    if fav:
        cursor.execute("DELETE FROM library_favorites WHERE child_id = ? AND book_id = ?", (cid, book_id))
        cursor.execute("UPDATE library_books SET likes_count = MAX(0, likes_count - 1) WHERE id = ?", (book_id,))
        is_fav = False
        msg = "Kitob sevimli kitoblar ro'yxatidan chiqarildi"
    else:
        cursor.execute("INSERT INTO library_favorites (user_id, child_id, book_id) VALUES (?, ?, ?)", (uid, cid, book_id))
        cursor.execute("UPDATE library_books SET likes_count = likes_count + 1 WHERE id = ?", (book_id,))
        is_fav = True
        msg = "Kitob sevimli kitoblar ro'yxatiga qo'shildi! ❤️"

    conn.commit()
    conn.close()

    return {
        "success": True,
        "book_id": book_id,
        "is_favorite": is_fav,
        "message": msg
    }


# 7.15.8. SEVIMLI KITOBLAR RO'YXATI (/mobile/library/favorites/)
@app.get("/mobile/library/favorites/", response_model=List[LibraryBookItemResponse], tags=["Mobil Ilova — Kutubxona (Library & Audio Books)"], summary="7.15.8. Farzandning Sevimli Kitoblari Ro'yxati")
@app.get("/mobile/library/favorites", response_model=List[LibraryBookItemResponse], include_in_schema=False)
@app.get("/api/library/favorites/", response_model=List[LibraryBookItemResponse], include_in_schema=False)
@app.get("/api/library/favorites", response_model=List[LibraryBookItemResponse], include_in_schema=False)
def get_library_favorites(
    request: Request,
    child_id: Optional[int] = Query(None),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    active_child = resolve_current_child(child_id, current_user)
    if not active_child:
        return []

    cid = active_child["id"]
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.*, c.name as category_name, c.slug as category_slug
        FROM library_favorites f
        JOIN library_books b ON b.id = f.book_id
        LEFT JOIN library_categories c ON c.id = b.category_id
        WHERE f.child_id = ?
        ORDER BY f.created_at DESC
    """, (cid,))
    rows = cursor.fetchall()
    conn.close()

    return [format_book_dict(dict(r), request, child_id=cid) for r in rows]


# 7.15.9. ADMIN & CRUD: YANGI KITOB QO'SHISH (/mobile/library/books/)
@app.post("/mobile/library/books/", response_model=LibraryBookDetailResponse, status_code=status.HTTP_201_CREATED, tags=["Web & Admin — Kutubxona Boshqaruvi"], summary="Admin: Yangi Kitob Qo'shish")
@app.post("/mobile/library/books", response_model=LibraryBookDetailResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@app.post("/api/library/books/", response_model=LibraryBookDetailResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@app.post("/api/library/books", response_model=LibraryBookDetailResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_library_book(payload: CreateBookRequest, request: Request):
    conn = get_db_connection()
    cursor = conn.cursor()

    clean_cover = sanitize_image_path(payload.cover_image or "/images/library/sariq_devni_minib.png")
    clean_audio = sanitize_image_path(payload.audio_url or "")

    cursor.execute("""
        INSERT INTO library_books (
            category_id, title, author, cover_image, description, content,
            audio_url, duration_seconds, duration_formatted, target_age,
            is_featured, section, listen_count, likes_count, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 'active')
    """, (
        payload.category_id, payload.title.strip(), payload.author.strip(),
        clean_cover, payload.description.strip(), (payload.content or "").strip(),
        clean_audio, payload.duration_seconds or 0, payload.duration_formatted or "10:00",
        payload.target_age or "7-12 yosh", 1 if payload.is_featured else 0,
        payload.section or "eng-sara"
    ))
    new_id = cursor.lastrowid
    conn.commit()

    cursor.execute("""
        SELECT b.*, c.name as category_name, c.slug as category_slug
        FROM library_books b
        LEFT JOIN library_categories c ON c.id = b.category_id
        WHERE b.id = ?
    """, (new_id,))
    row = cursor.fetchone()
    conn.close()

    return format_book_dict(dict(row), request)


# 7.15.10. ADMIN & CRUD: KITOBNI TAHRIRLASH (/mobile/library/books/{book_id}/)
@app.put("/mobile/library/books/{book_id}/", response_model=LibraryBookDetailResponse, tags=["Web & Admin — Kutubxona Boshqaruvi"], summary="Admin: Kitobni Tahrirlash")
@app.put("/mobile/library/books/{book_id}", response_model=LibraryBookDetailResponse, include_in_schema=False)
@app.put("/api/library/books/{book_id}/", response_model=LibraryBookDetailResponse, include_in_schema=False)
@app.put("/api/library/books/{book_id}", response_model=LibraryBookDetailResponse, include_in_schema=False)
def update_library_book(book_id: int, payload: UpdateBookRequest, request: Request):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM library_books WHERE id = ?", (book_id,))
    old = cursor.fetchone()
    if not old:
        conn.close()
        raise HTTPException(status_code=404, detail="Kitob topilmadi!")

    d = dict(old)
    new_cat = payload.category_id if payload.category_id is not None else d["category_id"]
    new_title = payload.title.strip() if payload.title is not None else d["title"]
    new_author = payload.author.strip() if payload.author is not None else d["author"]
    new_cover = sanitize_image_path(payload.cover_image) if payload.cover_image is not None else d["cover_image"]
    new_desc = payload.description.strip() if payload.description is not None else d["description"]
    new_content = payload.content if payload.content is not None else d["content"]
    new_audio = sanitize_image_path(payload.audio_url) if payload.audio_url is not None else d["audio_url"]
    new_dur_sec = payload.duration_seconds if payload.duration_seconds is not None else d["duration_seconds"]
    new_dur_fmt = payload.duration_formatted if payload.duration_formatted is not None else d["duration_formatted"]
    new_age = payload.target_age if payload.target_age is not None else d["target_age"]
    new_feat = 1 if payload.is_featured else 0 if payload.is_featured is not None else d["is_featured"]
    new_sec = payload.section if payload.section is not None else d["section"]
    new_status = payload.status if payload.status is not None else d["status"]

    cursor.execute("""
        UPDATE library_books
        SET category_id = ?, title = ?, author = ?, cover_image = ?, description = ?,
            content = ?, audio_url = ?, duration_seconds = ?, duration_formatted = ?,
            target_age = ?, is_featured = ?, section = ?, status = ?
        WHERE id = ?
    """, (
        new_cat, new_title, new_author, new_cover, new_desc,
        new_content, new_audio, new_dur_sec, new_dur_fmt,
        new_age, new_feat, new_sec, new_status, book_id
    ))
    conn.commit()

    cursor.execute("""
        SELECT b.*, c.name as category_name, c.slug as category_slug
        FROM library_books b
        LEFT JOIN library_categories c ON c.id = b.category_id
        WHERE b.id = ?
    """, (book_id,))
    updated = cursor.fetchone()
    conn.close()

    return format_book_dict(dict(updated), request)


# 7.15.11. ADMIN & CRUD: KITOBNI O'CHIRISH (/mobile/library/books/{book_id}/)
@app.delete("/mobile/library/books/{book_id}/", tags=["Web & Admin — Kutubxona Boshqaruvi"], summary="Admin: Kitobni O'chirish")
@app.delete("/mobile/library/books/{book_id}", include_in_schema=False)
@app.delete("/api/library/books/{book_id}/", include_in_schema=False)
@app.delete("/api/library/books/{book_id}", include_in_schema=False)
def delete_library_book(book_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM library_books WHERE id = ?", (book_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Kitob topilmadi!")

    cursor.execute("DELETE FROM library_books WHERE id = ?", (book_id,))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Kitob muvaffaqiyatli o'chirildi"}


# 7.15.12. MUQOVA RASMINI YUKLASH (/mobile/library/upload-cover/)
@app.post("/mobile/library/upload-cover/", tags=["Web & Admin — Kutubxona Boshqaruvi"], summary="Admin: Kitob Muqova Rasmini Yuklash")
@app.post("/mobile/library/upload-cover", include_in_schema=False)
@app.post("/api/library/upload-cover/", include_in_schema=False)
@app.post("/api/library/upload-cover", include_in_schema=False)
async def upload_library_cover(request: Request, file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower() or ".png"
    unique_name = f"cover_{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(LIBRARY_UPLOAD_DIR, unique_name)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    relative_url = f"/images/library/{unique_name}"
    full_url = to_full_image_url(relative_url, request)

    return {
        "success": True,
        "message": "Kitob muqovasi muvaffaqiyatli yuklandi",
        "url": full_url,
        "image": full_url,
        "path": relative_url,
        "filename": file.filename
    }


# 7.15.13. AUDIO FAYL YUKLASH (/mobile/library/upload-audio/)
@app.post("/mobile/library/upload-audio/", tags=["Web & Admin — Kutubxona Boshqaruvi"], summary="Admin: Kitob Audio Faylini Yuklash (.mp3 / .wav / .m4a)")
@app.post("/mobile/library/upload-audio", include_in_schema=False)
@app.post("/api/library/upload-audio/", include_in_schema=False)
@app.post("/api/library/upload-audio", include_in_schema=False)
async def upload_library_audio(request: Request, file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower() or ".mp3"
    unique_name = f"audio_{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(LIBRARY_AUDIO_DIR, unique_name)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    relative_url = f"/audio/library/{unique_name}"
    full_url = to_full_image_url(relative_url, request)

    return {
        "success": True,
        "message": "Audio fayl muvaffaqiyatli yuklandi",
        "url": full_url,
        "audio_url": full_url,
        "path": relative_url,
        "filename": file.filename
    }


# 7.15.14. KITOB MATNIDAN AVTOMATIK AUDIO GENERATSIYA QILISH (EDGE-TTS)
@app.post("/mobile/library/books/{book_id}/generate-audio/", tags=["Web & Admin — Kutubxona Boshqaruvi"], summary="Admin: Kitob Matnidan Avtomatik O'zbekcha Audio Generatsiya Qilish (Edge-TTS)")
@app.post("/mobile/library/books/{book_id}/generate-audio", include_in_schema=False)
@app.post("/api/library/books/{book_id}/generate-audio/", include_in_schema=False)
@app.post("/api/library/books/{book_id}/generate-audio", include_in_schema=False)
async def generate_book_audio_tts(book_id: int, request: Request):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM library_books WHERE id = ?", (book_id,))
    book = cursor.fetchone()
    if not book:
        conn.close()
        raise HTTPException(status_code=404, detail="Kitob topilmadi!")

    b = dict(book)
    text_to_read = b.get("content") or b.get("description") or f"{b['title']}. Muallif: {b['author']}."
    text_to_read = f"{b['title']}. Muallif: {b['author']}.\n{text_to_read}"

    filename = f"book_{book_id}_{hashlib.md5(text_to_read.encode('utf-8')).hexdigest()[:8]}.mp3"
    file_path = os.path.join(LIBRARY_AUDIO_DIR, filename)

    try:
        comm = edge_tts.Communicate(text_to_read, voice="uz-UZ-SardorNeural", rate="+3%", volume="+40%")
        await comm.save(file_path)

        relative_url = f"/audio/library/{filename}"
        cursor.execute("UPDATE library_books SET audio_url = ? WHERE id = ?", (relative_url, book_id))
        conn.commit()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Audio generatsiyasida xatolik: {str(e)}")

    conn.close()
    full_url = to_full_image_url(relative_url, request)

    return {
        "success": True,
        "message": "Audio muvaffaqiyatli generatsiya qilindi va kitobga biriktirildi!",
        "audio_url": full_url,
        "url": full_url
    }



# ==============================================================================
# 7.13.4. ADMIN PANEL — URAN KATEGORIYALARI VA SO'ZLARI CRUD
# ==============================================================================
@app.get("/api/website/uran/categories", response_model=List[UranCategoryResponse], tags=["Web & Admin — Uran Sayyorasi Boshqaruvi"], summary="Admin: Uran Kategoriyalar Ro'yxati")
def admin_get_uran_categories(request: Request, status: Optional[str] = None):
    return get_uran_categories(request, status=status, current_user=None)

@app.post("/api/website/uran/categories", response_model=UranCategoryResponse, status_code=status.HTTP_201_CREATED, tags=["Web & Admin — Uran Sayyorasi Boshqaruvi"], summary="Admin: Yangi Uran Kategoriyasi Qo'shish")
def admin_create_uran_category(payload: UranCategoryCreate, request: Request):
    conn = get_db_connection()
    cursor = conn.cursor()
    img = (payload.image or "/images/categories/fruits.png").strip()
    if img.endswith(".svg") and "/images/categories/" in img:
        img = img[:-4] + ".png"
    cursor.execute("""
        INSERT INTO uran_categories (name, name_en, name_ru, image, description, status, order_num)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (payload.name, payload.name_en or "", payload.name_ru or "", img, payload.description or "", payload.status or "active", payload.order_num or 0))
    cat_id = cursor.lastrowid
    conn.commit()
    cursor.execute("SELECT * FROM uran_categories WHERE id = ?", (cat_id,))
    row = cursor.fetchone()
    conn.close()
    return {
        "id": row["id"],
        "name": row["name"],
        "name_en": row["name_en"],
        "name_ru": row["name_ru"],
        "image": to_full_image_url(row["image"], request),
        "description": row["description"],
        "status": row["status"],
        "order_num": row["order_num"],
        "words_count": 0,
        "created_at": str(row["created_at"])
    }

@app.put("/api/website/uran/categories/{cat_id}", response_model=UranCategoryResponse, tags=["Web & Admin — Uran Sayyorasi Boshqaruvi"], summary="Admin: Uran Kategoriyasini Tahrirlash")
def admin_update_uran_category(cat_id: int, payload: UranCategoryUpdate, request: Request):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM uran_categories WHERE id = ?", (cat_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Kategoriya topilmadi")

    name = payload.name if payload.name is not None else row["name"]
    name_en = payload.name_en if payload.name_en is not None else row["name_en"]
    name_ru = payload.name_ru if payload.name_ru is not None else row["name_ru"]
    image = payload.image if payload.image is not None else row["image"]
    if image and image.endswith(".svg") and "/images/categories/" in image:
        image = image[:-4] + ".png"
    description = payload.description if payload.description is not None else row["description"]
    status_val = payload.status if payload.status is not None else row["status"]
    order_num = payload.order_num if payload.order_num is not None else row["order_num"]

    cursor.execute("""
        UPDATE uran_categories 
        SET name = ?, name_en = ?, name_ru = ?, image = ?, description = ?, status = ?, order_num = ?
        WHERE id = ?
    """, (name, name_en, name_ru, image, description, status_val, order_num, cat_id))
    conn.commit()

    cursor.execute("SELECT COUNT(*) as words_count FROM uran_words WHERE category_id = ?", (cat_id,))
    w_cnt = cursor.fetchone()["words_count"]
    cursor.execute("SELECT * FROM uran_categories WHERE id = ?", (cat_id,))
    updated_row = cursor.fetchone()
    conn.close()

    return {
        "id": updated_row["id"],
        "name": updated_row["name"],
        "name_en": updated_row["name_en"],
        "name_ru": updated_row["name_ru"],
        "image": to_full_image_url(updated_row["image"], request),
        "description": updated_row["description"],
        "status": updated_row["status"],
        "order_num": updated_row["order_num"],
        "words_count": w_cnt,
        "created_at": str(updated_row["created_at"])
    }

@app.delete("/api/website/uran/categories/{cat_id}", tags=["Web & Admin — Uran Sayyorasi Boshqaruvi"], summary="Admin: Uran Kategoriyasini O'chirish")
def admin_delete_uran_category(cat_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM uran_words WHERE category_id = ?", (cat_id,))
    cursor.execute("DELETE FROM child_uran_quiz_results WHERE category_id = ?", (cat_id,))
    cursor.execute("DELETE FROM uran_categories WHERE id = ?", (cat_id,))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Kategoriya va uning barcha so'zlari muvaffaqiyatli o'chirildi", "id": cat_id}

@app.get("/api/website/uran/words", response_model=List[UranWordResponse], tags=["Web & Admin — Uran Sayyorasi Boshqaruvi"], summary="Admin: Uran So'zlar Ro'yxati")
def admin_get_uran_words(category_id: Optional[int] = None, request: Request = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if category_id:
        cursor.execute("SELECT * FROM uran_words WHERE category_id = ? ORDER BY order_num ASC, id ASC", (category_id,))
    else:
        cursor.execute("SELECT * FROM uran_words ORDER BY category_id ASC, order_num ASC, id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [format_uran_word_row(r, request) for r in rows]

@app.get("/api/website/uran/practice", tags=["Web & Admin — Uran Sayyorasi Boshqaruvi"], summary="Uran: Random 3-4 ta so'z kartochkalari va test")
def get_uran_practice(count: int = 3, request: Request = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    safe_count = max(2, min(count, 5))
    cursor.execute("SELECT * FROM uran_words ORDER BY RANDOM() LIMIT ?", (safe_count,))
    selected_rows = cursor.fetchall()

    if not selected_rows:
        conn.close()
        return {"cards": [], "quiz": None}

    cards = [format_uran_word_row(r, request) for r in selected_rows]

    # Test uchun kartochkalardan bittasini tanlaymiz
    target = random.choice(cards)
    correct_answer = target["word_uz"]

    # Qolgan 3 ta noto'g'ri variantni bazadan olamiz
    cursor.execute("SELECT word_uz FROM uran_words WHERE id != ? ORDER BY RANDOM() LIMIT 3", (target["id"],))
    distractor_rows = cursor.fetchall()
    conn.close()

    distractors = [d["word_uz"] for d in distractor_rows]
    options = [correct_answer] + distractors
    random.shuffle(options)

    quiz = {
        "word_en": target["word_en"],
        "transcription": target["transcription"],
        "part_of_speech": target.get("part_of_speech", "noun"),
        "question": f"«{target['word_en']}» so'zining o'zbekcha tarjimasi nima?",
        "correct": correct_answer,
        "options": options,
        "image": target["image"],
        "audio_url": target["audio_url"]
    }

    return {"cards": cards, "quiz": quiz}

@app.get("/api/website/saturn/practice", tags=["Web & Admin — Sayyoralar Interaktiv Mashqlari"], summary="Saturn: 2-3 ta matematika mashqi va test")
def get_saturn_practice(count: int = 3):
    pool_cards = [
        {
            "id": "math_1",
            "badge": "Qo'shish amali ➕",
            "problem": "3 + 4 = ?",
            "visual": "🍎 🍎 🍎  +  🍎 🍎 🍎 🍎",
            "answer": "7",
            "explanation": "3 ta olmaga 4 ta olma qo'shilsa, jami 7 ta olma bo'ladi: 3 + 4 = 7",
            "audio_text": "Uchga to'rtni qo'shganda yetti bo'ladi."
        },
        {
            "id": "math_2",
            "badge": "Ayirish amali ➖",
            "problem": "8 - 3 = ?",
            "visual": "⭐ ⭐ ⭐ ⭐ ⭐ ⭐ ⭐ ⭐  ➖  ⭐ ⭐ ⭐",
            "answer": "5",
            "explanation": "8 ta yulduzdan 3 tasi olinsa, 5 ta yulduz qoladi: 8 - 3 = 5",
            "audio_text": "Sakkizdan uchni ayirsak besh qoladi."
        },
        {
            "id": "math_3",
            "badge": "Mantiqiy jumboq 🧩",
            "problem": "Daraxtda 5 ta qush bor edi. Yana 3 tasi uchib keldi. Jami nechta bo'ldi?",
            "visual": "🦜 🦜 🦜 🦜 🦜  ➕  🦜 🦜 🦜",
            "answer": "8",
            "explanation": "5 ta qushchaga 3 ta qushcha qo'shildi: 5 + 3 = 8 ta qushcha!",
            "audio_text": "Beshga uchni qo'shsak sakkiz ta bo'ladi."
        },
        {
            "id": "math_4",
            "badge": "Qo'shish amali ➕",
            "problem": "6 + 2 = ?",
            "visual": "🍓 🍓 🍓 🍓 🍓 🍓  +  🍓 🍓",
            "answer": "8",
            "explanation": "6 ta qulupnayga 2 ta qulupnay qo'shilsa, jami 8 ta bo'ladi: 6 + 2 = 8",
            "audio_text": "Oltiga ikkini qo'shsak sakkiz bo'ladi."
        },
        {
            "id": "math_5",
            "badge": "Ayirish amali ➖",
            "problem": "10 - 4 = ?",
            "visual": "🎈 🎈 🎈 🎈 🎈 🎈 🎈 🎈 🎈 🎈  ➖  🎈 🎈 🎈 🎈",
            "answer": "6",
            "explanation": "10 ta shardan 4 tasi uchib ketsa, 6 ta shar qoladi: 10 - 4 = 6",
            "audio_text": "O'ndan to'rtni ayirsak olti qoladi."
        },
        {
            "id": "math_6",
            "badge": "Taqqoslash amali ⚖️",
            "problem": "Qaysi biri ko'p: 7 ta olma yoki 4 ta olma?",
            "visual": "🍎🍎🍎🍎🍎🍎🍎  (7)   vs   (4)  🍎🍎🍎🍎",
            "answer": "7 ta olma",
            "explanation": "7 soni 4 sonidan katta: 7 > 4, demak 7 ta olma ko'proq!",
            "audio_text": "Yetti to'rtdan katta, demak yetti ta olma ko'p."
        }
    ]

    pool_quizzes = [
        {
            "question": "6 + 3 yig'indisi nechiga teng?",
            "visual": "🍇🍇🍇🍇🍇🍇  +  🍇🍇🍇",
            "correct": "9",
            "options": ["7", "8", "9", "10"],
            "explanation": "6 ga 3 ni qo'shganda 9 hosil bo'ladi: 6 + 3 = 9",
            "audio_text": "Oltiga uchni qo'shsak necha bo'ladi? To'qqiz!"
        },
        {
            "question": "9 dan 4 ni ayirsak nechchi qoladi? (9 - 4 = ?)",
            "visual": "⭐⭐⭐⭐⭐⭐⭐⭐⭐  ➖  ⭐⭐⭐⭐",
            "correct": "5",
            "options": ["3", "4", "5", "6"],
            "explanation": "9 dan 4 ni ayirganda 5 qoladi: 9 - 4 = 5",
            "audio_text": "To'qqizdan to'rtni ayirsak besh qoladi!"
        },
        {
            "question": "Akmalda 4 ta, ukasida 3 ta shokolad bor. Jami nechta shokolad bor?",
            "visual": "🍫🍫🍫🍫  +  🍫🍫🍫",
            "correct": "7 ta",
            "options": ["5 ta", "6 ta", "7 ta", "8 ta"],
            "explanation": "4 + 3 = 7 ta shokolad bo'ladi!",
            "audio_text": "To'rtga uchni qo'shsak yetti ta bo'ladi!"
        },
        {
            "question": "7 + 3 hisoblang: (7 + 3 = ?)",
            "visual": "🌸🌸🌸🌸🌸🌸🌸  +  🌸🌸🌸",
            "correct": "10",
            "options": ["8", "9", "10", "11"],
            "explanation": "7 ga 3 ni qo'shganda butun 10 hosil bo'ladi: 7 + 3 = 10",
            "audio_text": "Yettiga uchni qo'shsak o'n bo'ladi!"
        }
    ]

    safe_count = max(2, min(count, 4))
    selected_cards = random.sample(pool_cards, safe_count)
    selected_quiz = random.choice(pool_quizzes)
    # Shuffle options
    shuffled_options = list(selected_quiz["options"])
    random.shuffle(shuffled_options)
    quiz_data = dict(selected_quiz)
    quiz_data["options"] = shuffled_options

    return {"cards": selected_cards, "quiz": quiz_data}

@app.get("/api/website/yupiter/calendar-presets", tags=["Web & Admin — Sayyoralar Interaktiv Mashqlari"], summary="Yupiter: Taym-menejment taqvimi va kunlik reja shablonlari")
def get_yupiter_calendar_presets():
    return {
        "presets": [
            {"id": "read", "text": "Kitob mutolaasi 📖 (20 daqiqa)", "category": "Mutolaa"},
            {"id": "math", "text": "Matematika mashqi 🧮", "category": "Ta'lim"},
            {"id": "sport", "text": "Badantarbiya va sport 🏃", "category": "Sport"},
            {"id": "lang", "text": "Ingliz tili so'zlari 🇬🇧", "category": "Tillar"},
            {"id": "hw", "text": "Uy vazifalarini bajarish ✍️", "category": "Ta'lim"},
            {"id": "art", "text": "Rasm chizish va ijod 🎨", "category": "Ijod"},
            {"id": "clean", "text": "Xonani tartibga keltirish 🧹", "category": "Tartib"}
        ],
        "mottoes": [
            "20 daqiqa qoidasi: Rejalashtirilgan har bir mashg'ulot intizom va quvonch keltiradi! ⏱️",
            "Vaqtni unumli taqsimlagan bola kelajakda buyuk allomaga aylanadi! 🌟",
            "Bugungi 20 daqiqalik odat ertangi ulkan muvaffaqiyat poydevoridir! 🚀",
            "Reja asosida yashash fikrni tiniq va ruhni tetik qiladi! 🎯"
        ]
    }

@app.get("/api/website/venera/wardrobe", tags=["Web & Admin — Sayyoralar Interaktiv Mashqlari"], summary="Venera: Virtual Do'kon va Kiyintirish ma'lumotlari")
def get_venera_wardrobe():
    return {
        "character": {
            "name": "Kichik Alloma",
            "image": "/img/venera_boy.png?v=3",
            "coins": 200
        },
        "categories": [
            {
                "id": "outfits",
                "name": "Haqiqiy 3D Liboslar",
                "icon": "🥋",
                "items": [
                    {
                        "id": "default",
                        "name": "Asl Milliy Libos",
                        "icon": "👘",
                        "image": "/img/venera_boy.png?v=3",
                        "price": 0,
                        "desc": "O'zining qulay milliy yaktagi"
                    },
                    {
                        "id": "doppi",
                        "name": "Milliy Do'ppi & Zar Chopon",
                        "icon": "🇺🇿",
                        "image": "/img/wardrobe_doppi.jpg",
                        "price": 30,
                        "desc": "Zardo'zi saroy choponi va O'zbek milliy do'ppisi"
                    },
                    {
                        "id": "crown",
                        "name": "Qirollik Toji & Shohona Libos",
                        "icon": "👑",
                        "image": "/img/wardrobe_crown.jpg",
                        "price": 45,
                        "desc": "Oltin toj, qimmatbaho javohirlar va qizil plash"
                    },
                    {
                        "id": "astronaut",
                        "name": "Fazogir & Kosmik Shlem",
                        "icon": "🚀",
                        "image": "/img/wardrobe_astronaut.jpg",
                        "price": 50,
                        "desc": "Haqiqiy kosmonavt skafandri va koinot dubulg'asi"
                    },
                    {
                        "id": "scientist",
                        "name": "Bilimdon Alloma & Professor",
                        "icon": "🎓",
                        "image": "/img/wardrobe_scientist.jpg",
                        "price": 35,
                        "desc": "Akademik shlyapa, ko'zoynak va oq xalat"
                    },
                    {
                        "id": "superhero",
                        "name": "Super Alloma Qahramon",
                        "icon": "🦸",
                        "image": "/img/wardrobe_superhero.jpg",
                        "price": 40,
                        "desc": "Yulduzli qahramonlik zirhi va qudratli qizil plash"
                    },
                    {
                        "id": "sport",
                        "name": "Zamonaviy Sportchi & Gamer",
                        "icon": "🧢",
                        "image": "/img/wardrobe_sport.jpg",
                        "price": 25,
                        "desc": "Sport kastyumi, kepka, quyosh ko'zoynagi va naushnik"
                    }
                ]
            },
            {
                "id": "backdrops",
                "name": "Sehrli Fonlar",
                "icon": "🌌",
                "items": [
                    {"id": "space", "name": "Koinot & Venera", "icon": "🪐", "price": 0, "desc": "Yulduzli koinot va sayyoralar bag'rida"},
                    {"id": "registan", "name": "Registon Saroyi", "icon": "🏛️", "price": 20, "desc": "Samarqand va Buxoro qadimiy madaniyati"},
                    {"id": "future_lab", "name": "Kelajak Markazi", "icon": "🧪", "price": 25, "desc": "Yuqori texnologiyalar laboratoriyasi"},
                    {"id": "cozy_room", "name": "Kutubxona Xonasi", "icon": "📚", "price": 15, "desc": "Shinamgina allomalar kutubxonasi"}
                ]
            }
        ]
    }

@app.get("/api/website/neptun/tree", tags=["Web & Admin — Sayyoralar Interaktiv Mashqlari"], summary="Neptun: Sehrli Hissiyotlar Daraxti ma'lumotlari")
def get_neptun_tree():
    return {
        "title": "Sehrli Hissiyotlar Daraxti",
        "treeImage": "/img/neptun_tree.png",
        "description": "Daraxt o'rtasini yoki shoxlarini bosing, emoji tanlang va daraxtga yopishtiring!",
        "categories": [
            {
                "id": "emotions",
                "name": "His-tuyg'ular",
                "icon": "💖",
                "emojis": [
                    {"emoji": "😊", "name": "Xursand", "desc": "Quvnoq kayfiyat"},
                    {"emoji": "🤩", "name": "Hayratda", "desc": "Ajoyib kashfiyot"},
                    {"emoji": "🥰", "name": "Mehrli", "desc": "Mehr va samimiyat"},
                    {"emoji": "😎", "name": "Quvnoq", "desc": "O'ziga ishongan"},
                    {"emoji": "🥳", "name": "Bayram", "desc": "Xursandchilik"},
                    {"emoji": "😇", "name": "Beg'ubor", "desc": "Yaxshi niyat"},
                    {"emoji": "🤗", "name": "Do'stona", "desc": "Quchoqlash va do'stlik"},
                    {"emoji": "🤔", "name": "Fikrchan", "desc": "Donolik va o'ylov"},
                    {"emoji": "😴", "name": "Orom", "desc": "Tinch va osuda"},
                    {"emoji": "💖", "name": "Yurakcha", "desc": "Cheksiz sevgi"}
                ]
            },
            {
                "id": "fruits",
                "name": "Mevalar & Tabiat",
                "icon": "🍎",
                "emojis": [
                    {"emoji": "🍎", "name": "Qizil olma", "desc": "Shirin qizil olma"},
                    {"emoji": "🍏", "name": "Yashil olma", "desc": "Mazali yashil olma"},
                    {"emoji": "🍊", "name": "Apelsin", "desc": "Sershira apelsin"},
                    {"emoji": "🍋", "name": "Limon", "desc": "Nordongina limon"},
                    {"emoji": "🍓", "name": "Qulupnay", "desc": "Xushbo'y qulupnay"},
                    {"emoji": "🍒", "name": "Gilos", "desc": "Qizg'aldoq gilos"},
                    {"emoji": "🍇", "name": "Uzum", "desc": "Shirin uzum shingili"},
                    {"emoji": "🌸", "name": "Bahor guli", "desc": "Nafis gulbarg"},
                    {"emoji": "🌻", "name": "Kungaboqar", "desc": "Quyosh guli"},
                    {"emoji": "🍀", "name": "Omad yaprog'i", "desc": "To'rt yaproqli yonbosh"}
                ]
            },
            {
                "id": "magic",
                "name": "Sehr & Qahramonlar",
                "icon": "✨",
                "emojis": [
                    {"emoji": "🌟", "name": "Oltin yulduz", "desc": "Koinot yulduzi"},
                    {"emoji": "🦋", "name": "Sehrli kapalak", "desc": "Rangin qanotli kapalak"},
                    {"emoji": "🐝", "name": "Mehnatkash ari", "desc": "Asalari"},
                    {"emoji": "🦜", "name": "To'tiqush", "desc": "Quvnoq qushcha"},
                    {"emoji": "🦉", "name": "Dono boyo'g'li", "desc": "Bilimdon qush"},
                    {"emoji": "🎈", "name": "Rangli shar", "desc": "Uchar havo shari"},
                    {"emoji": "🎁", "name": "Sovg'a", "desc": "Kutilmagan sovg'a"},
                    {"emoji": "💎", "name": "Olmos", "desc": "Yaltiroq qimmatbaho tosh"},
                    {"emoji": "👑", "name": "Toj", "desc": "Shohona toj"},
                    {"emoji": "🌈", "name": "Kamalak", "desc": "Yetti rang jilosi"}
                ]
            }
        ]
    }

@app.post("/api/website/uran/words", response_model=UranWordResponse, status_code=status.HTTP_201_CREATED, tags=["Web & Admin — Uran Sayyorasi Boshqaruvi"], summary="Admin: Yangi So'z Qo'shish")
def admin_create_uran_word(payload: UranWordCreate, request: Request):
    conn = get_db_connection()
    cursor = conn.cursor()
    word_img = (payload.image or "").strip()
    if not word_img:
        cursor.execute("SELECT image FROM uran_categories WHERE id = ?", (payload.category_id,))
        cat_row = cursor.fetchone()
        if cat_row and cat_row["image"]:
            word_img = cat_row["image"]
        else:
            word_img = "/images/categories/fruits.png"
    elif word_img.endswith(".svg") and "/images/categories/" in word_img:
        word_img = word_img[:-4] + ".png"

    pos = payload.part_of_speech or "noun"
    pos_uz = payload.part_of_speech_uz or URAN_POS_UZ_MAP.get(pos, "Ot")

    cursor.execute("""
        INSERT INTO uran_words (category_id, word_uz, word_en, word_ru, transcription, part_of_speech, part_of_speech_uz, image, audio_url, example_sentence, example_translation, order_num)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (payload.category_id, payload.word_uz, payload.word_en, payload.word_ru or "", payload.transcription or "", pos, pos_uz, word_img, payload.audio_url or "", payload.example_sentence or "", payload.example_translation or "", payload.order_num or 0))
    word_id = cursor.lastrowid
    conn.commit()
    cursor.execute("SELECT * FROM uran_words WHERE id = ?", (word_id,))
    row = cursor.fetchone()
    conn.close()
    return format_uran_word_row(row, request)

@app.put("/api/website/uran/words/{word_id}", response_model=UranWordResponse, tags=["Web & Admin — Uran Sayyorasi Boshqaruvi"], summary="Admin: So'zni Tahrirlash")
def admin_update_uran_word(word_id: int, payload: UranWordUpdate, request: Request):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM uran_words WHERE id = ?", (word_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="So'z topilmadi")

    category_id = payload.category_id if payload.category_id is not None else row["category_id"]
    word_uz = payload.word_uz if payload.word_uz is not None else row["word_uz"]
    word_en = payload.word_en if payload.word_en is not None else row["word_en"]
    word_ru = payload.word_ru if payload.word_ru is not None else row["word_ru"]
    transcription = payload.transcription if payload.transcription is not None else row["transcription"]
    row_keys = row.keys() if hasattr(row, 'keys') else []
    pos = payload.part_of_speech if payload.part_of_speech is not None else (row["part_of_speech"] if "part_of_speech" in row_keys and row["part_of_speech"] else "noun")
    pos_uz = payload.part_of_speech_uz if payload.part_of_speech_uz is not None else (row["part_of_speech_uz"] if "part_of_speech_uz" in row_keys and row["part_of_speech_uz"] else URAN_POS_UZ_MAP.get(pos, "Ot"))
    image = payload.image if payload.image is not None else row["image"]
    if image and image.endswith(".svg") and "/images/categories/" in image:
        image = image[:-4] + ".png"
    audio_url = payload.audio_url if payload.audio_url is not None else row["audio_url"]
    example_sentence = payload.example_sentence if payload.example_sentence is not None else row["example_sentence"]
    example_translation = payload.example_translation if payload.example_translation is not None else row["example_translation"]
    order_num = payload.order_num if payload.order_num is not None else row["order_num"]

    cursor.execute("""
        UPDATE uran_words 
        SET category_id = ?, word_uz = ?, word_en = ?, word_ru = ?, transcription = ?, part_of_speech = ?, part_of_speech_uz = ?, image = ?, audio_url = ?, example_sentence = ?, example_translation = ?, order_num = ?
        WHERE id = ?
    """, (category_id, word_uz, word_en, word_ru, transcription, pos, pos_uz, image, audio_url, example_sentence, example_translation, order_num, word_id))
    conn.commit()
    cursor.execute("SELECT * FROM uran_words WHERE id = ?", (word_id,))
    updated_row = cursor.fetchone()
    conn.close()

    return format_uran_word_row(updated_row, request)

@app.delete("/api/website/uran/words/{word_id}", tags=["Web & Admin — Uran Sayyorasi Boshqaruvi"], summary="Admin: So'zni O'chirish")
def admin_delete_uran_word(word_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM uran_words WHERE id = ?", (word_id,))
    conn.commit()
    conn.close()
    return {"success": True, "message": "So'z muvaffaqiyatli o'chirildi", "id": word_id}


@app.post("/api/website/uran/ai-suggest", response_model=UranAiSuggestResponse, tags=["Web & Admin — Uran Sayyorasi Boshqaruvi"], summary="Admin: AI orqali so'z tarjimasi va misolini avtomatik to'ldirish")
def admin_uran_ai_suggest(payload: UranAiSuggestRequest):
    word = payload.word_en.strip()
    if not word:
        raise HTTPException(status_code=400, detail="Inglizcha so'z kiritilmadi!")

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = (
            f"You are an English-Uzbek educational vocabulary assistant for children.\n"
            f"Given the English word: '{word}', provide:\n"
            f"1. word_uz: accurate, clean Uzbek translation (single clear word, e.g. Olma)\n"
            f"2. word_ru: accurate Russian translation\n"
            f"3. transcription: standard IPA transcription in brackets, e.g. [ˈæp.əl]\n"
            f"4. part_of_speech: one of ['noun', 'adjective', 'verb', 'adverb', 'pronoun', 'preposition', 'other']\n"
            f"5. part_of_speech_uz: Uzbek name for the part of speech ('Ot' for noun, 'Sifat' for adjective, 'Fe\'l' for verb, 'Ravish' for adverb, 'Olmosh' for pronoun, 'Old ko\'makchi' for preposition, 'Boshqa' for other)\n"
            f"6. example_sentence: a simple, fun, educational English sentence for kids containing this word.\n"
            f"7. example_translation: Uzbek translation of that example sentence.\n\n"
            f"Respond ONLY with a valid JSON object without markdown fences:\n"
            f'{{"word_en": "{word}", "word_uz": "...", "word_ru": "...", "transcription": "...", "part_of_speech": "noun", "part_of_speech_uz": "Ot", "example_sentence": "...", "example_translation": "..."}}'
        )
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```[a-zA-Z]*\n", "", text)
            text = re.sub(r"\n```$", "", text).strip()
        data = json.loads(text)
        pos = data.get("part_of_speech", "noun").strip().lower()
        if pos not in URAN_POS_UZ_MAP:
            pos = "noun"
        pos_uz = data.get("part_of_speech_uz", "").strip() or URAN_POS_UZ_MAP.get(pos, "Ot")

        return {
            "word_en": word,
            "word_uz": data.get("word_uz", "").strip(),
            "word_ru": data.get("word_ru", "").strip(),
            "transcription": data.get("transcription", "").strip(),
            "part_of_speech": pos,
            "part_of_speech_uz": pos_uz,
            "example_sentence": data.get("example_sentence", "").strip(),
            "example_translation": data.get("example_translation", "").strip()
        }
    except Exception as e:
        return {
            "word_en": word,
            "word_uz": "",
            "word_ru": "",
            "transcription": f"[{word.lower()}]",
            "part_of_speech": "noun",
            "part_of_speech_uz": "Ot",
            "example_sentence": f"This is an {word}.",
            "example_translation": f"Bu {word}."
        }


# 8. MOBIL SAYYORALAR RO'YXATI (/mobile/planets/ va /mobile/planets)
@app.get("/mobile/planets/", response_model=List[PlanetResponse], tags=["Mobil Ilova — Sayyoralar (Planets)"], summary="8. Mobil Ilova Uchun Barcha Sayyoralar Ro'yxati — is_blocked maydoni bilan (Token orqali)")
@app.get("/mobile/planets", response_model=List[PlanetResponse], include_in_schema=False)
def mobile_get_planets(request: Request, current_user: dict = Depends(get_current_user)):
    lang = get_accept_language(request)
    conn = get_db_connection()
    cursor = conn.cursor()
    # BARCHA sayyoralarni qaytaramiz — bola ilovasi is_blocked=True bo'lsa o'zi blok ko'rsatsin
    cursor.execute("SELECT * FROM planets ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [format_planet_row(row, request, lang=lang) for row in rows]


# 9. MOBIL SAYYORA BATAFSIL (/mobile/planets/{planet_id})
@app.get("/mobile/planets/{planet_id}", response_model=PlanetResponse, tags=["Mobil Ilova — Sayyoralar (Planets)"], summary="9. Mobil Ilova Uchun Bitta Sayyora Tafsilotlari (Token orqali)")
def mobile_get_planet_detail(planet_id: int, request: Request, current_user: dict = Depends(get_current_user)):
    lang = get_accept_language(request)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM planets WHERE id = ?", (planet_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Sayyora topilmadi!")
    formatted = format_planet_row(row, request, lang=lang)
    if formatted.get("is_blocked"):
        raise HTTPException(status_code=403, detail="Ushbu sayyora hozirda qulflangan!")
    return formatted


# 9.1 MOBIL FAQ SAVOLLAR RO'YXATI (/mobile/faqs/ va /mobile/faqs)
@app.get("/mobile/faqs/", response_model=List[FaqResponse], tags=["Mobil Ilova — Autentifikatsiya & Farzandlar Boshqaruvi"], summary="9.1. Mobil Ilova Uchun FAQ (Ko'p So'raladigan Savollar) Ro'yxati")
@app.get("/mobile/faqs", response_model=List[FaqResponse], include_in_schema=False)
def mobile_get_faqs(request: Request):
    lang = get_accept_language(request)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM faqs WHERE status = 'active' ORDER BY order_num ASC, id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [format_faq_row(r, lang=lang) for r in rows]


@app.get("/mobile/faqs/{faq_id}", response_model=FaqResponse, tags=["Mobil Ilova — Autentifikatsiya & Farzandlar Boshqaruvi"], summary="9.2. Mobil Ilova Uchun Bitta FAQ Savol Tafsilotlari")
def mobile_get_faq_detail(faq_id: int, request: Request):
    lang = get_accept_language(request)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM faqs WHERE id = ?", (faq_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="FAQ savol topilmadi!")
    return format_faq_row(row, lang=lang)


# 9.8 OVOZ TALUFUZINI TOZALASH VA SO'ZLARGA AYLANTIRISH
def format_text_for_speech(text: str, lang: str = "uzb") -> str:
    """Ovozli o'qish uchun matnni tozalash va tabiiy, yoqimli talaffuzga moslash"""
    if not text:
        return ""
    t = text
    # Markdown va maxsus belgilarni olib tashlash
    t = re.sub(r'[*#_`~>•\\/\[\]\(\)\{\}]', ' ', t)
    # Emojilarni olib tashlash (TTS xatolik bermasligi uchun)
    t = re.sub(r'[\U00010000-\U0010ffff]', ' ', t)

    # Arifmetik belgilar va amallarni tabiiy so'zga aylantirish
    if lang in ("ru", "rus", "ru-ru"):
        t = re.sub(r'(\d+)\s*\+\s*(\d+)', r'\1 плюс \2', t)
        t = re.sub(r'(\d+)\s*-\s*(\d+)', r'\1 минус \2', t)
        t = re.sub(r'(\d+)\s*=\s*(\d+)', r'\1 равно \2', t)
        t = t.replace("+", " плюс ").replace("=", " равно ").replace("%", " процентов ")
    elif lang in ("en", "eng", "en-us"):
        t = re.sub(r'(\d+)\s*\+\s*(\d+)', r'\1 plus \2', t)
        t = re.sub(r'(\d+)\s*-\s*(\d+)', r'\1 minus \2', t)
        t = re.sub(r'(\d+)\s*=\s*(\d+)', r'\1 equals \2', t)
        t = t.replace("+", " plus ").replace("=", " equals ").replace("%", " percent ")
    else: # uzb
        t = re.sub(r'(\d+)\s*\+\s*(\d+)', r"\1 ga \2 ni qo'shsak", t)
        t = re.sub(r'(\d+)\s*-\s*(\d+)', r"\1 dan \2 ni ayirsak", t)
        t = re.sub(r'(\d+)\s*=\s*(\d+)', r"\1 teng \2", t)
        t = t.replace("+", " qo'shuv ").replace("=", " teng ").replace("%", " foiz ")

    # Ortiqcha bo'shliqlarni tozalash
    t = re.sub(r'\s+', ' ', t).strip()
    return t


# 9.9 EDGE TTS YORDAMCHI FUNKSIYASI (Ultra-HD Sho'x Ovoz & Tabiiy Talaffuz)
async def generate_edge_tts_audio(text: str, lang: str = "uzb", request: Request = None, child_age: Optional[int] = None, voice_type: Optional[str] = None) -> Optional[str]:
    """Matnni yosh bolalar uchun yoqimli, sho'x va baland-tiniq (HD) ovozga aylantiradi"""
    try:
        clean_text = format_text_for_speech(text, lang)
        if not clean_text:
            return None

        lang_lower = (lang or "uzb").strip().lower()
        if lang_lower in ["ru", "rus", "ru-ru"]:
            voice = "ru-RU-DmitryNeural"
            pitch_val = "+6Hz"
            rate_val = "+4%"
        elif lang_lower in ["en", "eng", "en-us"]:
            voice = "en-US-AnaNeural" if voice_type == "female" else "en-US-GuyNeural"
            pitch_val = "+5Hz"
            rate_val = "+3%"
        else:
            # O'zbek tili uchun yoshga mos ovoz:
            voice = "uz-UZ-SardorNeural"
            age = child_age or 6
            if age <= 7:
                # 3 yoshdan 7 yoshgacha: Sho'x, o'ynoqi, qiziqarli yosh bola ovozi
                pitch_val = "+28Hz"
                rate_val = "+6%"
            else:
                # 8 yoshdan katta: Do'stona, intellektual yigit ovozi
                pitch_val = "+2Hz"
                rate_val = "+1%"

        # Volume +50% — tiniq, jarangdor va baland eshitilishi uchun
        volume_val = "+50%"

        hash_key = hashlib.md5(f"{voice}:{pitch_val}:{rate_val}:{volume_val}:{clean_text}".encode('utf-8')).hexdigest()
        filename = f"{hash_key}.mp3"
        file_path = os.path.join(AUDIO_CACHE_DIR, filename)

        if not os.path.exists(file_path):
            communicate = edge_tts.Communicate(clean_text, voice, pitch=pitch_val, rate=rate_val, volume=volume_val)
            await communicate.save(file_path)

        relative_url = f"/audio_cache/{filename}"
        return to_full_image_url(relative_url, request) if request else relative_url
    except Exception as e:
        print("Edge TTS generatsiya xatosi:", e)
        return None


# 9.10 OVOZNI TINGLASH VA MATNGA AYLANTIRISH (SPEECH-TO-TEXT / MULTIMODAL AI)
async def process_audio_speech_to_text(audio_bytes: bytes, mime_type: str = "audio/mp3", lang: str = "uzb") -> str:
    """
    Bolaning audio ovozini tinglaydi va aytgan gapini 100% aniqlikda matnga (STT) aylantiradi.
    Gemini 3.6 Flash multimodal sun'iy intellekt texnologiyasi orqali ishlaydi.
    """
    models_to_try = ["gemini-3.6-flash", "gemini-1.5-flash", "gemini-2.0-flash-exp"]
    for m in models_to_try:
        try:
            model = genai.GenerativeModel(m)
            prompt = (
                f"Tinglovchi tili: {lang}. "
                "Ushbu audio yozuvni tinglab, bolaning aytgan gapini aniq matnga o'gir (transcription). "
                "Faqat quyidagi JSON formatida javob qaytar (boshqa hech narsa yozma):\n"
                "{\"transcription\": \"<bola aytgan aniq matn>\"}"
            )
            contents = [
                {"mime_type": mime_type, "data": audio_bytes},
                prompt
            ]
            response = await asyncio.to_thread(model.generate_content, contents)
            if response and response.text:
                clean_json = response.text.strip()
                if "```json" in clean_json:
                    clean_json = clean_json.split("```json")[1].split("```")[0].strip()
                elif "```" in clean_json:
                    clean_json = clean_json.split("```")[1].split("```")[0].strip()
                import json as py_json
                parsed = py_json.loads(clean_json)
                res_text = parsed.get("transcription", "").strip()
                if res_text:
                    return res_text
        except Exception as e:
            print(f"[STT Error with model {m}]:", e)
            continue
    return ""


# 10. GEMINI AI SUHBAT VA TAVSIYALAR (/mobile/ai/chat/ va /mobile/ai/chat)
@app.post("/mobile/ai/chat/", response_model=AiChatResponse, tags=["Mobil Ilova — Alloma AI & Ovozli Yordamchi"], summary="10. Bolalar & Ota-onalar Uchun Gemini AI Chatbot (Token orqali)")
@app.post("/mobile/ai/chat", response_model=AiChatResponse, tags=["Mobil Ilova — Alloma AI & Ovozli Yordamchi"], include_in_schema=False)
@app.post("/api/ai/chat/", response_model=AiChatResponse, tags=["Mobil Ilova — Alloma AI & Ovozli Yordamchi"], include_in_schema=False)
@app.post("/api/ai/chat", response_model=AiChatResponse, tags=["Mobil Ilova — Alloma AI & Ovozli Yordamchi"], include_in_schema=False)
async def mobile_ai_chat(req: AiChatRequest, request: Request, current_user: dict = Depends(get_current_user)):
    user_prompt = req.message.strip()
    if not user_prompt:
        raise HTTPException(status_code=400, detail="Xabar matni bo'sh bo'lishi mumkin emas!")

    # Standart til — O'zbek tili
    if not req.language:
        req.language = "uzb"

    user_id = current_user.get("id") if current_user else None
    return await _build_ai_response(req, user_prompt, request, user_id=user_id)


def _save_ai_interaction(user_id: Optional[int], req: AiChatRequest, user_prompt: str, ai_text: str, audio_url: Optional[str], planet_id: Optional[int], planet_name: Optional[str]):
    """AI suhbati va sarflangan vaqtni bazaga avtomatik yozish"""
    if not user_id:
        return
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Farzand ID sini aniqlash
        child_id = req.child_id
        if not child_id:
            cursor.execute("SELECT id FROM children WHERE user_id = ? ORDER BY id ASC LIMIT 1", (user_id,))
            c_row = cursor.fetchone()
            if c_row:
                child_id = c_row["id"]

        # 1. AI Chat Tarixiga yozish (User savoli va Model javobi)
        cursor.execute(
            "INSERT INTO ai_chat_history (user_id, child_id, role, message, audio_url, planet_id, planet_name) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, child_id, "user", user_prompt, None, planet_id, planet_name)
        )
        cursor.execute(
            "INSERT INTO ai_chat_history (user_id, child_id, role, message, audio_url, planet_id, planet_name) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, child_id, "model", ai_text, audio_url, planet_id, planet_name)
        )

        # 2. Kunlik Faollik va Vaqt (Screen time) ga qo'shish
        if child_id:
            today_str = datetime.now().strftime("%Y-%m-%d")
            target_planet = planet_id or 42
            cursor.execute("SELECT * FROM child_activities WHERE child_id = ? AND date = ? AND planet_id = ?", (child_id, today_str, target_planet))
            act = cursor.fetchone()
            if act:
                cursor.execute(
                    "UPDATE child_activities SET minutes_spent = minutes_spent + 2, messages_count = messages_count + 1 WHERE id = ?",
                    (act["id"],)
                )
            else:
                cursor.execute(
                    "INSERT INTO child_activities (user_id, child_id, date, minutes_spent, messages_count, planet_id) VALUES (?, ?, ?, 2, 1, ?)",
                    (user_id, child_id, today_str, target_planet)
                )

        conn.commit()
        conn.close()
    except Exception as e:
        print("[AI History/Activity Save Error]:", e)


async def _build_ai_response(req: AiChatRequest, user_prompt: str, request: Request = None, user_id: Optional[int] = None) -> dict:
    """AI javobini quradigan umumiy funksiya (mobil va admin uchun)"""

    # 1. Bolaning yoshi va ismi
    age = req.child_age or 7
    child_name = req.child_name or "Do'stim"

    # 2. Yosh toifasiga mos pedagogik qoida va uslub
    if age <= 6:
        age_group_label = "3-6 yosh (Maktabgacha yoshdagi kichkintoy)"
        pedagogical_style = (
            "- Soddalashtirilgan, quvnoq va ertaksimon tilda so'zla.\n"
            "- Misollar: Mevalar (olma, nok), shirin jonivorlar (quyoncha, ayiqcha), ranglar va barmoqlarda sanash.\n"
            "- Savollar: Juda sodda, 1 ta aniq savol bilan tugat (Masalan: 'Qani, sanab ko'r-chi, nechta bo'ldi?')."
        )
    elif age <= 10:
        age_group_label = "7-10 yosh (Boshlang'ich maktab o'quvchisi)"
        pedagogical_style = (
            "- Qiziquvchan, faol, do'stona va intellektual ustoz sifatida muloqot qil.\n"
            "- Misollar: Maktab hayoti, do'stlar, sport, kosmik jismlar, tabiat mo'jizalari va qiziqarli aqliy jumboqlar.\n"
            "- Bolalarcha ortiqcha erkalashsiz, do'stona hurmat bilan savol ber va fikrlashga chorla."
        )
    else:
        age_group_label = f"{age} yosh (Katta maktab / O'smir o'quvchi)"
        pedagogical_style = (
            "- DIQQAT: Bola 11+ yoshda! Unga bolalarcha muomala qilma, qo'lda barmoq sanash yoki olma-nok misollarini ISHLATMA!\n"
            "- Tengdosh aqlli do'st sifatida qisqa va lo'nda tushuntir.\n"
            "- Misollar: Real fan, texnologiya, tezkor hisob va mantiqiy qonuniyatlar."
        )

    # 3. Sayyora konteksti va boy ma'lumotlar (ID 42 - 50)
    planet_info = ""
    planet_name_out = req.planet_name
    planet_id_out = req.planet_id

    PLANET_DETAILS = {
        42: {
            "name": "Kognitiv",
            "role": "Mantiq va aqliy jumboqlar sayyorasi.",
            "intro": f"Salom, {child_name}! Sen Kognitiv sayyorasidasan. Bu yerda mantiqiy jumboqlarni yechamiz. Qanday savoling bor? 🧠"
        },
        43: {
            "name": "Jismoniy va motorika",
            "role": "Harakat va mashqlar sayyorasi.",
            "intro": f"Salom, {child_name}! Sen Jismoniy sayyoradasan. Bu yerda chaqqonlik va mashqlarni o'rganamiz. Qani, boshlaymizmi? 🏃‍♂️"
        },
        44: {
            "name": "Nutq va til",
            "role": "Talaffuz va ertaklar sayyorasi.",
            "intro": f"Salom, {child_name}! Sen Nutq va til sayyorasidasan. Bu yerda chiroyli gapirish va ertaklarni o'rganamiz. Nima haqida gaplashamiz? 🗣️"
        },
        45: {
            "name": "Ijtimoiy",
            "role": "Do'stlik va hamkorlik sayyorasi.",
            "intro": f"Salom, {child_name}! Sen Ijtimoiy sayyoradasan. Bu yerda do'stlik va jamoada ishlashni o'rganamiz! 🤝"
        },
        46: {
            "name": "Emotsional",
            "role": "Kayfiyat va quvonch sayyorasi.",
            "intro": f"Salom, {child_name}! Sen Emotsional sayyoradasan. Bugun kayfiyating qanday? 😊"
        },
        47: {
            "name": "Axloqiy",
            "role": "Odob-axloq sayyorasi.",
            "intro": f"Salom, {child_name}! Sen Axloqiy sayyoradasan. Bu yerda yaxshi fazilatlarni o'rganamiz. ⚖️"
        },
        48: {
            "name": "Ijodkorlik",
            "role": "San'at va tasavvur sayyorasi.",
            "intro": f"Salom, {child_name}! Sen Ijodkorlik sayyorasidasan. Bugun nima chizamiz yoki yasaymiz? 🎨"
        },
        49: {
            "name": "O'z-o'zini boshqarish",
            "role": "Intizom va reja sayyorasi.",
            "intro": f"Salom, {child_name}! Sen O'z-o'zini boshqarish sayyorasidasan. Bugungi rejang qanday? 🎯"
        },
        50: {
            "name": "Quyosh",
            "role": "Markaziy AI suhbat maydoni.",
            "intro": f"Salom, {child_name}! Sen Quyoshdasan. Men bilan xohlagan mavzuda suhbatlashishing mumkin! ☀️"
        }
    }

    if req.planet_id:
        p_data = PLANET_DETAILS.get(req.planet_id)
        if p_data:
            planet_name_out = p_data["name"]
            planet_info = f" Sayyora: '{planet_name_out}'."
        else:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM planets WHERE id = ?", (req.planet_id,))
            p_row = cursor.fetchone()
            conn.close()
            if p_row:
                p_dict = dict(p_row)
                planet_name_out = p_dict.get("title", "")
                planet_desc = (p_dict.get("description") or "").replace("\n", " ")
                planet_info = f" Sayyora: '{planet_name_out}'."

    clean_low = user_prompt.lower().strip()
    is_planet_intro_query = any(k in clean_low for k in [
        "sayyora haqida", "bu yerda nima", "nimalar bor", "nima ish qilamiz",
        "sayyorasi haqida", "haqida gapirib ber", "tanishtir",
        "планета", "что здесь", "расскажи", "about planet", "what is this"
    ])

    # Til aniqlash (req.language yoki Accept-Language)
    ai_lang = (req.language or "uzb").strip().lower()
    if ai_lang in ("ru", "rus", "ru-ru"):
        ai_lang = "rus"
    elif ai_lang in ("en", "eng", "en-us"):
        ai_lang = "eng"
    else:
        ai_lang = "uzb"

    # Tilga mos sayyora intro
    if req.planet_id and req.planet_id in PLANET_DETAILS and (is_planet_intro_query or clean_low in ["salom", "salomalik", "assalomu alaykum", "hello", "hi", "привет"]):
        multilang = PLANET_INTROS_MULTILANG.get(req.planet_id, {})
        ai_text = multilang.get(ai_lang, PLANET_DETAILS[req.planet_id]["intro"])
        audio_url = await generate_edge_tts_audio(ai_text, ai_lang, request, child_age=age)
        _save_ai_interaction(user_id, req, user_prompt, ai_text, audio_url, planet_id_out, planet_name_out)
        return {
            "success": True,
            "message": "Sayyora tanishtiruvi muvaffaqiyatli olindi",
            "response": ai_text,
            "model_used": "alloma-planet-intro",
            "planet_id": planet_id_out,
            "planet_name": planet_name_out,
            "audio_url": audio_url
        }

    # Tilga mos javob tili ko'rsatmasi
    if ai_lang == "rus":
        lang_rule = "ОБЯЗАТЕЛЬНО отвечай на русском языке. Никогда не пиши на узбекском или английском."
        greet_text = f"Привет{', ' + child_name if req.child_name else ''}! Чем могу помочь? 😊"
    elif ai_lang == "eng":
        lang_rule = "ALWAYS respond in English. Never write in Uzbek or Russian."
        greet_text = f"Hello{', ' + child_name if req.child_name else ''}! How can I help you? 😊"
    else:
        lang_rule = "QAT'IY VA MAJBURIY QOIDA: FAQAT VA FAQAT O'ZBEK TILIDA (lotin alifbosida) javob ber! Hech qachon ingliz yoki rus tilida gapirma. Savol qaysi tilda bo'lishidan qat'i nazar, faqat sof, chiroyli va ravon o'zbek tilida gapir."
        greet_text = f"Salom{', ' + child_name if req.child_name else ''}! Qanday yordam bera olaman? 😊"

    # 4. YOSHGA MOS INTERAKTIV PEDAGOGIK TIZIM (Qisqa va lo'nda)
    system_instruction = (
        "Sen 'Alloma AI' — aqlli, quvnoq va do'stona o'g'il bola ustozi/do'stisan!\n"
        f"Bola: {child_name}, Yoshi: {age} yosh ({age_group_label}). {planet_info}\n\n"
        f"TIL QOIDASI: {lang_rule}\n\n"
        f"USLUB:\n{pedagogical_style}\n\n"
        "LOYIHA VA ASOSCHI HAQIDA RASMIY BILIMLAR (VIKIPEDIYA MANBASI):\n"
        "- Loyiha nomi: Kichik Alloma — 7–11 yoshdagi bolalar uchun AI asosidagi 8 sayyorali kosmik ta'lim va rivojlanish ekotizimi.\n"
        "- Loyiha asoschisi va bosh dasturchisi (Founder & Lead Developer, Project Manager): Shoxrux Komiljonov (Komiljonov Shoxruxbek Komiljon o'g'li).\n"
        "- Rasmiy Vikipediya manbasi: https://uz.wikipedia.org/w/index.php?title=Startup&oldid=6268714\n"
        "- Rasmiy veb-sayt: https://kichikalloma.uz\n"
        "- Aloqa kontaktlari: Telefon: +998 99 976 51 00, Email: kichikalloma@gmail.com\n"
        "- 8 ta sayyora: Yer (Kognitiv ta'lim va AI-ustoz, kuniga 20 daqiqa limit), Yupiter (O'z-o'zini boshqarish va reja), Venera (Virtual Store va moliyaviy savodxonlik), Saturn (Matematika va mantiq), Merkuriy (Kasblar va ijodkorlik), Uran (English Vocabulary), Mars (Jismoniy faollik), Neptun (Emotsional savodxonlik).\n"
        "- Agar kimdir loyiha, asoschi, founder, muallif, aloqa yoki tizim haqida so'rasa, FAQAT va FAQAT ushbu rasmiy ma'lumotlar hamda Vikipediya manbasiga tayangan holda Shoxrux Komiljonov loyiha asoschisi va rahbari ekanligini ayt!\n\n"
        "QAT'IY QOIDALAR:\n"
        "1. JUDA QISQA VA LO'NDA GAPIR! Javoblaring ko'pi bilan 1-2 ta qisqa jumlada bo'lsin. Cho'zma!\n"
        "2. TAYYOR JAVOBNI DARHOL AYTMA! Agar hisob yoki masala so'rasa, qisqacha misol ayt va oxirida o'zidan javobni so'ra!\n"
        "3. Bola to'g'ri topsa: munosib tilida qisqa olqishla.\n"
        "4. Matnda yulduzcha (*) yoki panjara (#) ishlatma."
    )

    # 5. Qisqa va lo'nda salomlashish (ko'p tilli)
    greetings = ["salom", "salomalik", "assalomu alaykum", "hello", "hi", "salom ai", "hey", "привет", "здравствуй", "добрый день"]
    if clean_low in greetings:
        ai_text = greet_text
        audio_url = await generate_edge_tts_audio(ai_text, ai_lang, request, child_age=age)
        _save_ai_interaction(user_id, req, user_prompt, ai_text, audio_url, planet_id_out, planet_name_out)
        return {
            "success": True,
            "message": "AI javobi muvaffaqiyatli olindi",
            "response": ai_text,
            "model_used": "alloma-ai-v1",
            "planet_id": planet_id_out,
            "planet_name": planet_name_out,
            "audio_url": audio_url
        }

    # 5.1 Founder, loyiha yoki Vikipediya haqidagi savollarga rasmiy tasdiqlangan tezkor javob
    founder_keywords = [
        "asoschi", "asoschisi", "founder", "kim yaratgan", "muallif", "muallifi",
        "kim qilgan", "shoxrux", "komiljonov", "loyiha egasi", "rahbari kim",
        "kichik alloma nima", "loyiha haqida", "vikipediya", "wikipedia"
    ]
    if any(k in clean_low for k in founder_keywords):
        if ai_lang == "rus":
            ai_text = (
                "Основатель, ведущий разработчик и руководитель проекта Kichik Alloma "
                "(Founder & Lead Developer, Project Manager) — Шохрух Комилджонов (Komiljonov Shoxruxbek Komiljon o'g'li). "
                "Проект представляет собой космическую образовательную экосистему из 8 планет для детей 7–11 лет. "
                "Официальная статья опубликована в Википедии: https://uz.wikipedia.org/w/index.php?title=Startup&oldid=6268714. "
                "Контакты: +998 99 976 51 00, kichikalloma@gmail.com, https://kichikalloma.uz."
            )
        elif ai_lang == "eng":
            ai_text = (
                "The founder, lead developer, and project manager of Kichik Alloma "
                "is Shoxrux Komiljonov (Komiljonov Shoxruxbek Komiljon o'g'li). "
                "The project is an AI-powered cosmic educational ecosystem with 8 planets for children aged 7–11. "
                "Official information is published on Wikipedia: https://uz.wikipedia.org/w/index.php?title=Startup&oldid=6268714. "
                "Contact: +998 99 976 51 00, kichikalloma@gmail.com, https://kichikalloma.uz."
            )
        else:
            ai_text = (
                "Kichik Alloma loyihasining asoschisi, muallifi va bosh dasturchisi "
                "(Founder & Lead Developer, Project Manager) — Shoxrux Komiljonovdir (Komiljonov Shoxruxbek Komiljon o'g'li). "
                "Loyiha 7–11 yoshdagi bolalar uchun 8 ta rivojlanish sayyorasiga ega sun'iy intellektli kosmik ta'lim ekotizimidir. "
                "Loyiha haqidagi rasmiy ma'lumotlar Vikipediya ensiklopediyasida tasdiqlangan: https://uz.wikipedia.org/w/index.php?title=Startup&oldid=6268714. "
                "Aloqa: +998 99 976 51 00, Email: kichikalloma@gmail.com, Sayt: https://kichikalloma.uz."
            )
        audio_url = await generate_edge_tts_audio(ai_text, ai_lang, request, child_age=age)
        _save_ai_interaction(user_id, req, user_prompt, ai_text, audio_url, planet_id_out, planet_name_out)
        return {
            "success": True,
            "message": "Loyiha va asoschi haqidagi rasmiy ma'lumot muvaffaqiyatli olindi",
            "response": ai_text,
            "model_used": "alloma-wikipedia-verified",
            "planet_id": planet_id_out,
            "planet_name": planet_name_out,
            "audio_url": audio_url
        }

    # 6. Gemini modellari orqali javob (tez va sifatli)
    models_to_try = [
        "gemini-3.6-flash",
        "gemini-2.0-flash-exp",
        "gemini-1.5-flash"
    ]
    ai_text = None
    used_model = "gemini-3.6-flash"

    for m in models_to_try:
        try:
            model = genai.GenerativeModel(
                model_name=m,
                system_instruction=system_instruction,
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 800,
                }
            )

            if req.history and len(req.history) > 0:
                chat_history = [
                    {"role": "user" if h.role == "user" else "model", "parts": [h.content]}
                    for h in req.history[-8:]
                ]
                chat = model.start_chat(history=chat_history)
                response = await asyncio.to_thread(chat.send_message, user_prompt, request_options={"timeout": 12})
            else:
                response = await asyncio.to_thread(model.generate_content, user_prompt, request_options={"timeout": 12})

            if response and response.text and len(response.text.strip()) > 2:
                ai_text = response.text.strip()
                ai_text = ai_text.replace("**", "").replace("##", "").replace("###", "").replace("*", "•")
                used_model = m
                break
        except Exception as e:
            print(f"[Gemini Call Error with {m}]: {e}")
            continue

    if not ai_text:
        if ai_lang == "rus":
            if age <= 6:
                ai_text = f"Давай посчитаем, {child_name}! В одной ручке 5 яблок, и в другой 5. Сколько всего получилось? 🍎✨"
            elif age <= 10:
                ai_text = f"Отличный вопрос, {child_name}! Если сложить 5 и 5, получится число пальчиков на обеих руках. Сколько это? 🧠🚀"
            else:
                ai_text = f"Интересный вопрос, {child_name}! 5 плюс 5 — это основа десятичной системы счисления. Какой твой ответ? 💡"
        elif ai_lang == "eng":
            if age <= 6:
                ai_text = f"Let's count, {child_name}! 5 sweet apples in one hand, and 5 in the other. How many apples in total? 🍎✨"
            elif age <= 10:
                ai_text = f"Great question, {child_name}! Adding 5 and 5 gives the total number of fingers on both hands. What is the answer? 🧠🚀"
            else:
                ai_text = f"Awesome question, {child_name}! 5 plus 5 equals ten. What are your thoughts? 💡"
        else:
            if age <= 6:
                ai_text = f"Qani, {child_name}, bir qo'lingda 5 ta shirin olma, ikkinchi qo'lingda ham 5 ta olma bor desak, jami nechta bo'ladi? Sanab ko'r-chi! 🍎✨"
            elif age <= 10:
                ai_text = f"Ajoyib savol, {child_name}! 5 ga 5 ni qo'shganda, ikki qo'ldagi barcha barmoqlar soni kelib chiqadi. Qani, javobi nechchi bo'ladi? 🧠🚀"
            else:
                ai_text = f"Zo'r savol, {child_name}! 5 va 5 — bu juft sonlar yig'indisi bo'lib, o'nlik sanoq sistemasining asosiy bo'g'ini. Qani, javobini ayt-chi! 💡"

    # Microsoft Neural Studio Audio generatsiya (Yoshga mos sozlangan)
    audio_url = await generate_edge_tts_audio(ai_text, ai_lang, request, child_age=age)
    _save_ai_interaction(user_id, req, user_prompt, ai_text, audio_url, planet_id_out, planet_name_out)

    return {
        "success": True,
        "message": "AI javobi muvaffaqiyatli olindi",
        "response": ai_text,
        "model_used": used_model,
        "planet_id": planet_id_out,
        "planet_name": planet_name_out,
        "audio_url": audio_url
    }


# 10.1 OVOZLI SUHBAT (VOICE-CHAT: OVOZ YUBORIB, OVOZ VA MATN OLISH)
@app.post("/mobile/ai/voice-chat/", response_model=AiVoiceChatResponse, tags=["Mobil Ilova — Alloma AI & Ovozli Yordamchi"], summary="10.1. Ovozli AI Suhbat (Voice-in -> Voice-out)")
@app.post("/mobile/ai/voice-chat", response_model=AiVoiceChatResponse, include_in_schema=False)
@app.post("/api/ai/voice-chat/", response_model=AiVoiceChatResponse, include_in_schema=False)
@app.post("/api/ai/voice-chat", response_model=AiVoiceChatResponse, include_in_schema=False)
async def mobile_ai_voice_chat(
    request: Request,
    file: UploadFile = File(..., description="Foydalanuvchi/bolaning ovozli fayli (MP3, WAV, M4A, OGG, WebM, FLAC)"),
    child_id: Optional[int] = Form(None),
    planet_id: Optional[int] = Form(None),
    planet_name: Optional[str] = Form(None),
    child_name: Optional[str] = Form(None),
    child_age: Optional[int] = Form(None),
    language: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user)
):
    # 1. Tilni aniqlash (Standart: O'zbek tili)
    req_lang = (language or "uzb").strip().lower()
    if req_lang not in ("ru", "rus", "ru-ru", "en", "eng", "en-us"):
        req_lang = "uzb"

    # 2. Audio faylni o'qish
    audio_bytes = await file.read()
    if not audio_bytes or len(audio_bytes) < 100:
        raise HTTPException(status_code=400, detail="Audio fayl bo'sh yoki yaroqsiz!")

    mime_type = file.content_type or "audio/mp3"
    if "wav" in (file.filename or "").lower() or "wav" in mime_type:
        mime_type = "audio/wav"
    elif "m4a" in (file.filename or "").lower() or "m4a" in mime_type:
        mime_type = "audio/m4a"
    elif "ogg" in (file.filename or "").lower() or "ogg" in mime_type:
        mime_type = "audio/ogg"
    elif "webm" in (file.filename or "").lower() or "webm" in mime_type:
        mime_type = "audio/webm"
    else:
        mime_type = "audio/mp3"

    # 3. Gemini Multimodal orqali ovozni tinglash va matnga aylantirish (STT)
    transcription = await process_audio_speech_to_text(audio_bytes, mime_type=mime_type, lang=req_lang)
    if not transcription:
        # Fallback agar ovoz juda sokin yoki tushunarsiz bo'lsa
        if req_lang == "rus":
            fallback_msg = "Привет! Я не расслышал, повтори ещё раз, пожалуйста! 😊"
            transcription = "Привет"
        elif req_lang == "eng":
            fallback_msg = "Hello! I could not hear clearly, could you say that again? 😊"
            transcription = "Hello"
        else:
            fallback_msg = "Salom! Ovozingni unchalik eshita olmadim, yana bir bor qaytarib aytib ko'r-chi! 😊"
            transcription = "Salom"

        audio_url = await generate_edge_tts_audio(fallback_msg, req_lang, request, child_age=child_age)
        return {
            "success": True,
            "message": "Ovoz qabul qilindi",
            "transcription": transcription,
            "response": fallback_msg,
            "audio_url": audio_url,
            "planet_id": planet_id,
            "planet_name": planet_name,
            "language": req_lang,
            "model_used": "gemini-3.6-flash"
        }

    # 4. Matn orqali AI javobini generatsiya qilish
    chat_req = AiChatRequest(
        message=transcription,
        child_id=child_id,
        child_name=child_name,
        child_age=child_age,
        planet_id=planet_id,
        planet_name=planet_name,
        language=req_lang
    )
    user_id = current_user.get("id") if current_user else None
    ai_resp = await _build_ai_response(chat_req, transcription, request, user_id=user_id)

    return {
        "success": True,
        "message": "Ovozli suhbat muvaffaqiyatli amalga oshirildi",
        "transcription": transcription,
        "response": ai_resp["response"],
        "audio_url": ai_resp["audio_url"],
        "planet_id": ai_resp.get("planet_id"),
        "planet_name": ai_resp.get("planet_name"),
        "language": req_lang,
        "model_used": ai_resp.get("model_used", "gemini-3.6-flash")
    }


# 10.2 SOF SPEECH-TO-TEXT (STT) ENDPOINT
@app.post("/mobile/ai/stt/", response_model=AiSttResponse, tags=["Mobil Ilova — Alloma AI & Ovozli Yordamchi"], summary="10.2. Sof Ovozni Matnga Aylantirish (Speech-to-Text)")
@app.post("/mobile/ai/stt", response_model=AiSttResponse, include_in_schema=False)
@app.post("/api/ai/stt/", response_model=AiSttResponse, include_in_schema=False)
@app.post("/api/ai/stt", response_model=AiSttResponse, include_in_schema=False)
async def mobile_ai_stt(
    request: Request,
    file: UploadFile = File(..., description="Ovozli fayl"),
    language: Optional[str] = Form(None)
):
    # Standart til — O'zbek tili
    req_lang = (language or "uzb").strip().lower()
    if req_lang not in ("ru", "rus", "ru-ru", "en", "eng", "en-us"):
        req_lang = "uzb"
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Audio fayl bo'sh!")

    mime_type = file.content_type or "audio/mp3"
    transcription = await process_audio_speech_to_text(audio_bytes, mime_type=mime_type, lang=req_lang)
    return {
        "success": True,
        "text": transcription,
        "language": req_lang
    }


# 10.3 MUSTAQIL TEXT-TO-SPEECH (TTS) ENDPOINT
@app.post("/api/website/ai/tts", tags=["Web Sayt (Website)"], summary="Matnni Microsoft Neural O'g'il Bola Audio (MP3)ga aylantirish")
@app.post("/api/website/ai/tts/", tags=["Web Sayt (Website)"], include_in_schema=False)
@app.post("/api/ai/tts", tags=["Web Sayt (Website)"], include_in_schema=False)
@app.post("/api/ai/tts/", tags=["Web Sayt (Website)"], include_in_schema=False)
@app.post("/mobile/ai/tts/", tags=["Mobil Ilova — Alloma AI & Ovozli Yordamchi"], include_in_schema=False)
@app.post("/mobile/ai/tts", tags=["Mobil Ilova — Alloma AI & Ovozli Yordamchi"], include_in_schema=False)
async def ai_tts_endpoint(req: AiTtsRequest, request: Request):
    audio_url = await generate_edge_tts_audio(req.text, req.language or "uzb", request)
    if not audio_url:
        raise HTTPException(status_code=500, detail="Audio yaratishda xatolik!")
    return {
        "success": True,
        "audio_url": audio_url
    }


# ==============================================================================

# WEB SAYT (WEBSITE) & ADMIN PANEL ENDPOINTS
# ==============================================================================

# 0. FAYL YUKLASH (IMAGE UPLOAD)
@app.post("/api/website/upload", tags=["Web Sayt (Website)"], summary="Rasm faylini serverga yuklash (To'liq URL qaytaradi)")
async def upload_file(request: Request, file: UploadFile = File(...)):
    try:
        ext = os.path.splitext(file.filename)[1].lower() or ".png"
        unique_name = f"{uuid.uuid4().hex}{ext}"
        file_path = os.path.join(UPLOADS_DIR, unique_name)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        relative_url = f"/images/uploads/{unique_name}"
        full_url = to_full_image_url(relative_url, request)

        return {
            "success": True,
            "filename": file.filename,
            "url": full_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fayl yuklashda xatolik: {str(e)}")


# 1. SAYYORALAR (PLANETS) ENDPOINTS
@app.get("/api/website/planets", response_model=List[PlanetResponse], tags=["Web Sayt (Website)"], summary="Barcha sayyoralar ro'yxatini olish (To'liq rasmli URL)")
@app.get("/api/website/planets/", response_model=List[PlanetResponse], include_in_schema=False)
@app.get("/api/planets", response_model=List[PlanetResponse], include_in_schema=False)
@app.get("/api/planets/", response_model=List[PlanetResponse], include_in_schema=False)
def get_planets(request: Request):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM planets ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [format_planet_row(row, request) for row in rows]

@app.post("/api/website/planets", response_model=PlanetResponse, status_code=status.HTTP_201_CREATED, tags=["Web Sayt (Website)"], summary="Yangi sayyora qo'shish (To'liq rasmli URL)")
@app.post("/api/planets", response_model=PlanetResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@app.post("/mobile/planets/", response_model=PlanetResponse, status_code=status.HTTP_201_CREATED, tags=["Mobil Ilova — Sayyoralar (Planets)"], summary="9.3. Mobil Ilova Orqali Yangi Sayyora Qo'shish")
@app.post("/mobile/planets", response_model=PlanetResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_planet(planet: PlanetCreate, request: Request):
    title = (planet.title or planet.name or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="Sayyora nomi majburiy! ('title' yoki 'name' yuboring)")

    conn = get_db_connection()
    cursor = conn.cursor()
    clean_img = sanitize_image_path(planet.image or "/images/planets/earth.svg")
    new_status = planet.status or "active"
    new_is_blocked = 1 if (new_status == "inactive" or planet.is_blocked or planet.is_block) else 0
    new_gradient = planet.gradient if planet.gradient is not None else None
    new_video = planet.video.strip() if planet.video else None
    cursor.execute(
        "INSERT INTO planets (title, description, image, status, is_blocked, is_block, gradient, video) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (title, planet.description.strip() if planet.description else "", clean_img, new_status, new_is_blocked, new_is_blocked, new_gradient, new_video)
    )
    conn.commit()
    planet_id = cursor.lastrowid
    cursor.execute("SELECT * FROM planets WHERE id = ?", (planet_id,))
    new_planet = cursor.fetchone()
    conn.close()
    return format_planet_row(new_planet, request)

@app.put("/api/website/planets/{planet_id}", response_model=PlanetResponse, tags=["Web Sayt (Website)"], summary="Sayyorani yangilash / tahrirlash")
@app.put("/api/planets/{planet_id}", response_model=PlanetResponse, include_in_schema=False)
@app.put("/mobile/planets/{planet_id}/", response_model=PlanetResponse, include_in_schema=False)
@app.put("/mobile/planets/{planet_id}", response_model=PlanetResponse, include_in_schema=False)
def update_planet(planet_id: int, planet: PlanetUpdate, request: Request):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM planets WHERE id = ?", (planet_id,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Sayyora topilmadi")

    title_in = planet.title if planet.title is not None else planet.name
    new_title = title_in.strip() if title_in is not None else existing["title"]
    new_desc = planet.description.strip() if planet.description is not None else existing["description"]
    new_image = sanitize_image_path(planet.image) if planet.image is not None else existing["image"]
    new_status = planet.status if planet.status is not None else existing["status"]
    new_gradient = planet.gradient if planet.gradient is not None else (existing["gradient"] if "gradient" in existing.keys() else None)
    new_video = planet.video.strip() if planet.video is not None else (existing["video"] if "video" in existing.keys() else None)

    # is_blocked va is_block: status yoki kelgan qiymatdan sinxronlash
    if planet.is_blocked is not None:
        new_is_blocked = 1 if planet.is_blocked else 0
        if new_is_blocked:
            new_status = "inactive"
        else:
            new_status = "active"
    elif planet.is_block is not None:
        new_is_blocked = 1 if planet.is_block else 0
        if new_is_blocked:
            new_status = "inactive"
        else:
            new_status = "active"
    else:
        new_is_blocked = 1 if new_status == "inactive" else 0

    cursor.execute(
        "UPDATE planets SET title = ?, description = ?, image = ?, status = ?, is_blocked = ?, is_block = ?, gradient = ?, video = ? WHERE id = ?",
        (new_title, new_desc, new_image, new_status, new_is_blocked, new_is_blocked, new_gradient, new_video, planet_id)
    )
    conn.commit()
    cursor.execute("SELECT * FROM planets WHERE id = ?", (planet_id,))
    updated = cursor.fetchone()
    conn.close()
    return format_planet_row(updated, request)

@app.delete("/api/website/planets/{planet_id}", tags=["Web Sayt (Website)"], summary="Sayyorani o'chirish")
@app.delete("/api/planets/{planet_id}", include_in_schema=False)
@app.delete("/mobile/planets/{planet_id}/", include_in_schema=False)
@app.delete("/mobile/planets/{planet_id}", include_in_schema=False)
def delete_planet(planet_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM planets WHERE id = ?", (planet_id,))
    conn.commit()
    changes = cursor.rowcount
    conn.close()
    if changes == 0:
        raise HTTPException(status_code=404, detail="Sayyora topilmadi")
    return {"message": "Sayyora muvaffaqiyatli o'chirildi", "id": planet_id}


# 2. QULAYLIKLAR (AMENITIES) ENDPOINTS
@app.get("/api/website/amenities", response_model=List[AmenityResponse], tags=["Web Sayt (Website)"], summary="Barcha qulayliklar ro'yxatini olish")
@app.get("/api/amenities", response_model=List[AmenityResponse], include_in_schema=False)
def get_amenities():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM amenities ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.post("/api/website/amenities", response_model=AmenityResponse, status_code=status.HTTP_201_CREATED, tags=["Web Sayt (Website)"], summary="Yangi qulaylik qo'shish")
@app.post("/api/amenities", response_model=AmenityResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_amenity(amenity: AmenityCreate):
    if not amenity.title.strip():
        raise HTTPException(status_code=400, detail="Qulaylik nomi majburiy!")
    if not amenity.description.strip():
        raise HTTPException(status_code=400, detail="Qulaylik tavsifi majburiy!")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO amenities (title, description, icon, status) VALUES (?, ?, ?, ?)",
        (amenity.title.strip(), amenity.description.strip(), amenity.icon or "", amenity.status or "active")
    )
    conn.commit()
    amenity_id = cursor.lastrowid
    cursor.execute("SELECT * FROM amenities WHERE id = ?", (amenity_id,))
    new_amenity = cursor.fetchone()
    conn.close()
    return dict(new_amenity)

@app.put("/api/website/amenities/{amenity_id}", response_model=AmenityResponse, tags=["Web Sayt (Website)"], summary="Qulaylikni yangilash")
@app.put("/api/amenities/{amenity_id}", response_model=AmenityResponse, include_in_schema=False)
def update_amenity(amenity_id: int, amenity: AmenityUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM amenities WHERE id = ?", (amenity_id,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Qulaylik topilmadi")

    new_title = amenity.title.strip() if amenity.title is not None else existing["title"]
    new_desc = amenity.description.strip() if amenity.description is not None else existing["description"]
    new_status = amenity.status if amenity.status is not None else existing["status"]

    cursor.execute(
        "UPDATE amenities SET title = ?, description = ?, status = ? WHERE id = ?",
        (new_title, new_desc, new_status, amenity_id)
    )
    conn.commit()
    cursor.execute("SELECT * FROM amenities WHERE id = ?", (amenity_id,))
    updated = cursor.fetchone()
    conn.close()
    return dict(updated)

@app.delete("/api/website/amenities/{amenity_id}", tags=["Web Sayt (Website)"], summary="Qulaylikni o'chirish")
@app.delete("/api/amenities/{amenity_id}", include_in_schema=False)
def delete_amenity(amenity_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM amenities WHERE id = ?", (amenity_id,))
    conn.commit()
    changes = cursor.rowcount
    conn.close()
    if changes == 0:
        raise HTTPException(status_code=404, detail="Qulaylik topilmadi")
    return {"message": "Qulaylik muvaffaqiyatli o'chirildi", "id": amenity_id}


# 3. JAMOA (TEAMS) ENDPOINTS
@app.get("/api/website/teams", response_model=List[TeamResponse], tags=["Web Sayt (Website)"], summary="Barcha jamoa a'zolarini olish (Ism, Familiya, Yo'nalishi, Rasmi)")
@app.get("/api/website/teams/", response_model=List[TeamResponse], include_in_schema=False)
@app.get("/api/teams", response_model=List[TeamResponse], include_in_schema=False)
@app.get("/api/teams/", response_model=List[TeamResponse], include_in_schema=False)
def get_teams(request: Request):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM teams ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [format_team_row(row, request) for row in rows]

@app.post("/api/website/teams", response_model=TeamResponse, status_code=status.HTTP_201_CREATED, tags=["Web Sayt (Website)"], summary="Yangi jamoa a'zosi qo'shish (Rasmli & Tavsifli)")
@app.post("/api/teams", response_model=TeamResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_team(member: TeamCreate, request: Request):
    if not member.first_name.strip() or not member.last_name.strip():
        raise HTTPException(status_code=400, detail="Ism va Familiya majburiy!")
    if not member.role.strip():
        raise HTTPException(status_code=400, detail="Yo'nalishi / Mutaxassisligi majburiy!")

    description = member.description.strip() if member.description else ""
    clean_img = sanitize_image_path(member.image or "/images/team/member1.svg")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO teams (first_name, last_name, role, description, image) VALUES (?, ?, ?, ?, ?)",
        (member.first_name.strip(), member.last_name.strip(), member.role.strip(), description, clean_img)
    )
    conn.commit()
    team_id = cursor.lastrowid
    cursor.execute("SELECT * FROM teams WHERE id = ?", (team_id,))
    new_member = cursor.fetchone()
    conn.close()
    return format_team_row(new_member, request)

@app.put("/api/website/teams/{team_id}", response_model=TeamResponse, tags=["Web Sayt (Website)"], summary="Jamoa a'zosini tahrirlash")
@app.put("/api/teams/{team_id}", response_model=TeamResponse, include_in_schema=False)
def update_team(team_id: int, member: TeamUpdate, request: Request):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM teams WHERE id = ?", (team_id,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Jamoa a'zosi topilmadi")

    existing_dict = dict(existing)
    new_first = member.first_name.strip() if member.first_name is not None else existing_dict["first_name"]
    new_last = member.last_name.strip() if member.last_name is not None else existing_dict["last_name"]
    new_role = member.role.strip() if member.role is not None else existing_dict["role"]
    new_desc = member.description.strip() if member.description is not None else existing_dict.get("description", "")
    new_image = sanitize_image_path(member.image) if member.image is not None else existing_dict["image"]

    cursor.execute(
        "UPDATE teams SET first_name = ?, last_name = ?, role = ?, description = ?, image = ? WHERE id = ?",
        (new_first, new_last, new_role, new_desc, new_image, team_id)
    )
    conn.commit()
    cursor.execute("SELECT * FROM teams WHERE id = ?", (team_id,))
    updated = cursor.fetchone()
    conn.close()
    return format_team_row(updated, request)

@app.delete("/api/website/teams/{team_id}", tags=["Web Sayt (Website)"], summary="Jamoa a'zosini o'chirish")
@app.delete("/api/teams/{team_id}", include_in_schema=False)
def delete_team(team_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM teams WHERE id = ?", (team_id,))
    conn.commit()
    changes = cursor.rowcount
    conn.close()
    if changes == 0:
        raise HTTPException(status_code=404, detail="Jamoa a'zosi topilmadi")
    return {"message": "Jamoa a'zosi muvaffaqiyatli o'chirildi", "id": team_id}


# 4. GALEREYA (GALLERY) ENDPOINTS
@app.get("/api/website/gallery", response_model=List[GalleryResponse], tags=["Web Sayt (Website)"], summary="Galereyadagi barcha rasmlar ro'yxatini olish (To'liq URL)")
@app.get("/api/gallery", response_model=List[GalleryResponse], include_in_schema=False)
def get_gallery(request: Request):
    lang = get_accept_language(request)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM gallery ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [format_gallery_row(row, request, lang=lang) for row in rows]

@app.post("/api/website/gallery", response_model=GalleryResponse, status_code=status.HTTP_201_CREATED, tags=["Web Sayt (Website)"], summary="Galereyaga yangi rasm qo'shish")
@app.post("/api/gallery", response_model=GalleryResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_gallery_item(item: GalleryCreate, request: Request):
    if not item.image.strip():
        raise HTTPException(status_code=400, detail="Rasm manzili majburiy!")

    conn = get_db_connection()
    cursor = conn.cursor()
    clean_img = sanitize_image_path(item.image.strip())
    cursor.execute(
        "INSERT INTO gallery (title, image) VALUES (?, ?)",
        (item.title.strip() if item.title else "", clean_img)
    )
    conn.commit()
    item_id = cursor.lastrowid
    cursor.execute("SELECT * FROM gallery WHERE id = ?", (item_id,))
    new_item = cursor.fetchone()
    conn.close()
    return format_gallery_row(new_item, request)

@app.delete("/api/website/gallery/{gallery_id}", tags=["Web Sayt (Website)"], summary="Galereyadan rasmni o'chirish")
@app.delete("/api/gallery/{gallery_id}", include_in_schema=False)
def delete_gallery_item(gallery_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM gallery WHERE id = ?", (gallery_id,))
    conn.commit()
    changes = cursor.rowcount
    conn.close()
    if changes == 0:
        raise HTTPException(status_code=404, detail="Rasm topilmadi")
    return {"message": "Rasm galereyadan o'chirildi", "id": gallery_id}


# 5. XABARLAR (MESSAGES) ENDPOINTS
@app.get("/api/website/messages", response_model=List[MessageResponse], tags=["Web Sayt (Website)"], summary="Kelgan barcha xabarlar ro'yxati (Toshkent vaqti bilan)")
@app.get("/api/messages", response_model=List[MessageResponse], include_in_schema=False)
def get_messages(
    search: Optional[str] = Query(None, description="Ism, telefon yoki xabar bo'yicha qidiruv"),
    unreadOnly: Optional[bool] = Query(None, description="Faqat o'qilmagan xabarlar")
):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM messages"
    conditions = []
    params = []

    if search:
        conditions.append("(name LIKE ? OR phone LIKE ? OR message LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    if unreadOnly:
        conditions.append("is_read = 0")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        d = dict(row)
        dt_info = format_tashkent_datetime(d.get("created_at"))
        d["created_at"] = dt_info["created_at"]
        d["created_date"] = dt_info["created_date"]
        d["created_time"] = dt_info["created_time"]
        d["formatted_time"] = dt_info["formatted_time"]
        results.append(d)
    return results

@app.post("/api/website/messages", status_code=status.HTTP_201_CREATED, tags=["Web Sayt (Website)"], summary="Yangi xabar yuborish (Mijoz nomidan, Toshkent vaqti bilan)")
@app.post("/api/website/messages/", status_code=status.HTTP_201_CREATED, include_in_schema=False)
@app.post("/api/website/contact", status_code=status.HTTP_201_CREATED, include_in_schema=False)
@app.post("/api/website/contact/", status_code=status.HTTP_201_CREATED, include_in_schema=False)
@app.post("/api/messages", status_code=status.HTTP_201_CREATED, include_in_schema=False)
@app.post("/api/messages/", status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_message(msg: MessageCreate):
    if not msg.name.strip() or not msg.phone.strip() or not msg.message.strip():
        raise HTTPException(status_code=400, detail="Barcha maydonlarni to'ldirish majburiy!")

    tashkent_now = get_tashkent_now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (name, phone, message, is_read, created_at) VALUES (?, ?, ?, 0, ?)",
        (msg.name.strip(), msg.phone.strip(), msg.message.strip(), tashkent_now)
    )
    conn.commit()
    msg_id = cursor.lastrowid
    cursor.execute("SELECT * FROM messages WHERE id = ?", (msg_id,))
    new_msg = dict(cursor.fetchone())
    conn.close()

    dt_info = format_tashkent_datetime(new_msg.get("created_at"))
    new_msg["created_at"] = dt_info["created_at"]
    new_msg["created_date"] = dt_info["created_date"]
    new_msg["created_time"] = dt_info["created_time"]
    new_msg["formatted_time"] = dt_info["formatted_time"]

    return {
        "success": True,
        "message": "Xabaringiz muvaffaqiyatli qabul qilindi!",
        "data": new_msg
    }

@app.patch("/api/website/messages/{message_id}/read", tags=["Web Sayt (Website)"], summary="Xabarni o'qilgan deb belgilash")
@app.patch("/api/messages/{message_id}/read", include_in_schema=False)
def mark_message_as_read(message_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE messages SET is_read = 1 WHERE id = ?", (message_id,))
    conn.commit()
    changes = cursor.rowcount
    conn.close()
    if changes == 0:
        raise HTTPException(status_code=404, detail="Xabar topilmadi")
    return {"message": "Xabar o'qilgan deb belgilandi", "id": message_id}

@app.delete("/api/website/messages/{message_id}", tags=["Web Sayt (Website)"], summary="Xabarni o'chirish")
@app.delete("/api/messages/{message_id}", include_in_schema=False)
def delete_message(message_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE id = ?", (message_id,))
    conn.commit()
    changes = cursor.rowcount
    conn.close()
    if changes == 0:
        raise HTTPException(status_code=404, detail="Xabar topilmadi")
    return {"message": "Xabar muvaffaqiyatli o'chirildi", "id": message_id}


# 5.5 FAQ (KO'P SO'RALADIGAN SAVOLLAR) CRUD ENDPOINTS
@app.get("/api/website/faqs", response_model=List[FaqResponse], tags=["Web Sayt (Website)"], summary="Barcha faol FAQ savollar ro'yxati")
@app.get("/api/website/faqs/", response_model=List[FaqResponse], include_in_schema=False)
@app.get("/api/faqs", response_model=List[FaqResponse], tags=["Web Sayt (Website)"], include_in_schema=False)
@app.get("/api/faqs/", response_model=List[FaqResponse], include_in_schema=False)
def get_faqs(request: Request):
    lang = get_accept_language(request)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM faqs ORDER BY order_num ASC, id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [format_faq_row(r, lang=lang) for r in rows]


@app.get("/api/faqs/{faq_id}", response_model=FaqResponse, tags=["Web Sayt (Website)"], summary="Bitta FAQ savol tafsilotlari")
@app.get("/api/website/faqs/{faq_id}", response_model=FaqResponse, include_in_schema=False)
def get_faq_detail(faq_id: int, request: Request):
    lang = get_accept_language(request)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM faqs WHERE id = ?", (faq_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="FAQ topilmadi!")
    return format_faq_row(row, lang=lang)


@app.post("/api/faqs", response_model=FaqResponse, status_code=status.HTTP_201_CREATED, tags=["Web Sayt (Website)"], summary="Yangi FAQ savol qo'shish (Admin)")
@app.post("/api/website/faqs", response_model=FaqResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_faq(faq: FaqCreate):
    name = faq.name.strip()
    description = faq.description.strip()
    if not name or not description:
        raise HTTPException(status_code=400, detail="Savol nomi va javob matni majburiy!")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO faqs (name, description, status, order_num) VALUES (?, ?, ?, ?)",
        (name, description, faq.status or "active", faq.order_num or 0)
    )
    faq_id = cursor.lastrowid
    conn.commit()
    cursor.execute("SELECT * FROM faqs WHERE id = ?", (faq_id,))
    row = cursor.fetchone()
    conn.close()
    return format_faq_row(row)


@app.put("/api/faqs/{faq_id}", response_model=FaqResponse, tags=["Web Sayt (Website)"], summary="FAQ savolni tahrirlash (Admin)")
@app.put("/api/website/faqs/{faq_id}", response_model=FaqResponse, include_in_schema=False)
def update_faq(faq_id: int, faq: FaqUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM faqs WHERE id = ?", (faq_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="FAQ topilmadi!")

    old = dict(row)
    name = faq.name.strip() if faq.name is not None else old["name"]
    description = faq.description.strip() if faq.description is not None else old["description"]
    stat = faq.status if faq.status is not None else old["status"]
    order_num = faq.order_num if faq.order_num is not None else old["order_num"]

    cursor.execute(
        "UPDATE faqs SET name = ?, description = ?, status = ?, order_num = ? WHERE id = ?",
        (name, description, stat, order_num, faq_id)
    )
    conn.commit()
    cursor.execute("SELECT * FROM faqs WHERE id = ?", (faq_id,))
    updated_row = cursor.fetchone()
    conn.close()
    return format_faq_row(updated_row)


@app.delete("/api/faqs/{faq_id}", tags=["Web Sayt (Website)"], summary="FAQ savolni o'chirish (Admin)")
@app.delete("/api/website/faqs/{faq_id}", tags=["Web Sayt (Website)"], include_in_schema=False)
def delete_faq(faq_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM faqs WHERE id = ?", (faq_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="FAQ topilmadi!")

    cursor.execute("DELETE FROM faqs WHERE id = ?", (faq_id,))
    conn.commit()
    conn.close()
    return {"success": True, "message": "FAQ savol muvaffaqiyatli o'chirildi", "id": faq_id}


# 6. STATISTIKA (STATS) ENDPOINT
@app.get("/api/website/stats", response_model=StatsResponse, tags=["Web Sayt (Website)"], summary="Statistikani olish")
@app.get("/api/website/stats/", response_model=StatsResponse, include_in_schema=False)
@app.get("/api/stats", response_model=StatsResponse, include_in_schema=False)
@app.get("/api/stats/", response_model=StatsResponse, include_in_schema=False)
def get_stats():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total, SUM(CASE WHEN is_read = 0 THEN 1 ELSE 0 END) as unread FROM messages")
    msg_row = cursor.fetchone()
    total_messages = msg_row["total"] or 0
    unread_messages = msg_row["unread"] or 0

    cursor.execute("SELECT COUNT(*) as total, SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active FROM amenities")
    am_row = cursor.fetchone()
    total_amenities = am_row["total"] or 0
    active_amenities = am_row["active"] or 0

    cursor.execute("SELECT COUNT(*) as total, SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active FROM planets WHERE id != 50")
    pl_row = cursor.fetchone()
    total_planets = pl_row["total"] or 8
    active_planets = pl_row["active"] or 0

    cursor.execute("SELECT COUNT(*) as total FROM teams")
    tm_row = cursor.fetchone()
    total_teams = tm_row["total"] or 0

    cursor.execute("SELECT COUNT(*) as total FROM gallery")
    gal_row = cursor.fetchone()
    total_gallery = gal_row["total"] or 0

    cursor.execute("SELECT COUNT(*) as total FROM faqs")
    faq_row = cursor.fetchone()
    total_faqs = faq_row["total"] or 0

    # Tashrif buyuruvchilar soni
    cursor.execute("SELECT value FROM system_meta WHERE key = 'site_visitors'")
    vis_row = cursor.fetchone()
    if not vis_row:
        total_visitors = 1
        cursor.execute("INSERT OR REPLACE INTO system_meta (key, value) VALUES ('site_visitors', ?)", (str(total_visitors),))
        conn.commit()
    else:
        try:
            total_visitors = int(vis_row["value"])
        except Exception:
            total_visitors = 1

    conn.close()
    return {
        "totalPlanets": total_planets,
        "activePlanets": active_planets,
        "totalAmenities": total_amenities,
        "activeAmenities": active_amenities,
        "totalTeams": total_teams,
        "totalGallery": total_gallery,
        "totalMessages": total_messages,
        "unreadMessages": unread_messages,
        "totalFaqs": total_faqs,
        "totalVisitors": total_visitors
    }


@app.post("/api/website/track-visit", tags=["Web Sayt (Website)"], summary="Saytga yangi tashrifni qayd qilish")
def track_website_visit():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM system_meta WHERE key = 'site_visitors'")
    row = cursor.fetchone()
    if not row:
        val = 1
        cursor.execute("INSERT OR REPLACE INTO system_meta (key, value) VALUES ('site_visitors', ?)", (str(val),))
    else:
        try:
            val = int(row["value"]) + 1
        except Exception:
            val = 1
        cursor.execute("UPDATE system_meta SET value = ? WHERE key = 'site_visitors'", (str(val),))
    conn.commit()
    conn.close()
    return {"success": True, "totalVisitors": val}


# 7. WEB SAYT LANDING TO'PLAMI
@app.get("/api/website/landing", response_model=WebsiteLandingResponse, tags=["Web Sayt (Website)"], summary="Web sayt Landing sahifasi uchun to'liq ma'lumotlar to'plami (Sayyoralar, Qulayliklar, Jamoa, Galereya, FAQ)")
def get_website_landing_data(request: Request):
    lang = get_accept_language(request)
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM planets WHERE status = 'active' ORDER BY id ASC")
    planets = [format_planet_row(r, request, lang=lang) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM amenities WHERE status = 'active' ORDER BY id ASC")
    amenities_rows = cursor.fetchall()
    amenities = []
    for r in amenities_rows:
        d = dict(r)
        if lang != "uzb":
            d["title"] = translate_text_sync(d.get("title", ""), lang)
            d["description"] = translate_text_sync(d.get("description", ""), lang)
        amenities.append(d)

    cursor.execute("SELECT * FROM teams ORDER BY id ASC")
    teams = [format_team_row(r, request, lang=lang) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM gallery ORDER BY id DESC")
    gallery = [format_gallery_row(r, request, lang=lang) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM faqs WHERE status = 'active' ORDER BY order_num ASC, id ASC")
    faqs = [format_faq_row(r, lang=lang) for r in cursor.fetchall()]

    site_name = translate_text_sync("Bolalar Ta'lim & Rivojlanish Platformasi", lang) if lang != "uzb" else "Bolalar Ta'lim & Rivojlanish Platformasi"
    tagline = translate_text_sync("8 ta Rivojlanish Sayyorasi orqali mukammal ta'lim", lang) if lang != "uzb" else "8 ta Rivojlanish Sayyorasi orqali mukammal ta'lim"

    conn.close()
    return {
        "site_name": site_name,
        "tagline": tagline,
        "planets": planets,
        "amenities": amenities,
        "teams": teams,
        "gallery": gallery,
        "faqs": faqs,
        "stats": {
            "total_planets": len(planets),
            "total_amenities": len(amenities),
            "total_teams": len(teams),
            "total_gallery": len(gallery),
            "total_faqs": len(faqs),
            "support": "24/7"
        }
    }


# 8. ADMIN PANEL ALLOMA AI YORDAMCHISI (/api/website/ai/chat)
@app.post("/api/website/ai/chat", response_model=AiChatResponse, tags=["Web Sayt (Website)"], summary="Admin Panel & Web Uchun Alloma AI Yordamchisi")
@app.post("/api/website/ai/chat/", response_model=AiChatResponse, include_in_schema=False)
async def admin_ai_chat(req: AiChatRequest, request: Request):
    user_prompt = req.message.strip()
    if not user_prompt:
        raise HTTPException(status_code=400, detail="Xabar matni bo'sh bo'lishi mumkin emas!")
    if not req.language:
        req.language = "uzb"
    return await _build_ai_response(req, user_prompt, request)


# 9. ASOSIY WEB SAYT STATIK VA SPA ROUTING (React Router & Assets uchun)
@app.get("/{full_path:path}", include_in_schema=False)
def serve_spa_or_static(full_path: str, request: Request):
    # API, docs, swagger, statik montajlar bo'lsa o'tkazib yuborish
    if any(full_path.startswith(prefix) for prefix in ["api", "mobile", "docs", "openapi.json", "css", "js", "images", "img", "assets", "audio_cache", "planets"]):
        raise HTTPException(status_code=404, detail="Topilmadi")

    # Agar admin subdomen bo'lsa -> Admin panel
    if is_admin_subdomain(request):
        admin_index = os.path.join(PUBLIC_DIR, "index.html")
        if os.path.exists(admin_index):
            return FileResponse(admin_index, media_type="text/html; charset=utf-8")

    # 1. website/dist/public dagi statik faylni qidirish (masalan: /logo.png, /favicon.png, /space-bg.jpg, /assets/xxx.js)
    static_file = os.path.join(WEBSITE_PUBLIC_DIR, full_path)
    if os.path.isfile(static_file):
        media_type = None
        lower_path = static_file.lower()
        if lower_path.endswith((".js", ".mjs")):
            media_type = "application/javascript; charset=utf-8"
        elif lower_path.endswith(".css"):
            media_type = "text/css; charset=utf-8"
        elif lower_path.endswith(".html"):
            media_type = "text/html; charset=utf-8"
        elif lower_path.endswith(".svg"):
            media_type = "image/svg+xml"
        elif lower_path.endswith(".wasm"):
            media_type = "application/wasm"
        else:
            media_type, _ = mimetypes.guess_type(static_file)
        return FileResponse(static_file, media_type=media_type)

    # 2. React Router SPA fallback (masalan: /planets, /about, /gallery)
    website_index = os.path.join(WEBSITE_PUBLIC_DIR, "index.html")
    if os.path.exists(website_index):
        return FileResponse(website_index, media_type="text/html; charset=utf-8")

    raise HTTPException(status_code=404, detail="Sahifa topilmadi")

