import json
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import sqlite3
import os

from .cache_manager import analytics_cache

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database.sqlite")

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA busy_timeout = 10000;")
    except Exception:
        pass
    return conn

def calc_age(year_raw: Any) -> int:
    """Tug'ilgan yili yoki sanasidan bolaning aniq yoshini hisoblash."""
    if not year_raw:
        return 7
    s = str(year_raw).strip()
    current_year = datetime.now().year
    # 1. 2018 yoki 2015 kabi to'rt xonali yil
    m = re.search(r'\b(19\d{2}|20\d{2})\b', s)
    if m:
        y = int(m.group(1))
        age = current_year - y
        if 2 <= age <= 18:
            return age
    # 2. To'g'ridan-to'g'ri yosh berilgan bo'lsa (masalan "7")
    if s.isdigit():
        val = int(s)
        if 2 <= val <= 18:
            return val
    return 7

def normalize_gender(raw_gender: Any) -> str:
    """Jinsni normallashtirish: 'boy' yoki 'girl'."""
    g = str(raw_gender or "").lower().strip()
    if any(k in g for k in ["male", "erkak", "ogil", "o'g'il", "boy", "o‘g‘il", "oʼgʼil"]):
        return "boy"
    if any(k in g for k in ["female", "ayol", "qiz", "girl", "qiz bola"]):
        return "girl"
    return "boy"

def get_child_profile(child_id: int) -> Optional[Dict[str, Any]]:
    """Bolaning profil ma'lumotlarini olish."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM children WHERE id = ?", (child_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    data = dict(row)
    data["age"] = calc_age(data.get("year"))
    data["gender_clean"] = normalize_gender(data.get("gender"))
    return data

def track_child_navigation(
    user_id: int,
    child_id: int,
    section_key: str,
    section_name: str,
    action_type: str = "view",
    extra_data: Optional[Dict] = None
) -> bool:
    """
    Bolaning qaysi bo'limga kirganini real-time qayd etish.
    (Frontend har bir sahifaga kirganda chaqiradi).
    """
    try:
        conn = get_db()
        cursor = conn.cursor()
        extra_json = json.dumps(extra_data or {}, ensure_ascii=False)
        cursor.execute(
            """
            INSERT INTO child_navigation_logs (user_id, child_id, section_key, section_name, action_type, extra_data)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, child_id, section_key, section_name, action_type, extra_json)
        )
        # Keshni tozalash
        analytics_cache.delete(f"live:{child_id}")
        analytics_cache.delete(f"analytics:{child_id}")
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[Track Navigation Error]: {e}")
        return False

def get_child_live_status(child_id: int) -> Dict[str, Any]:
    """
    Bolaning HOZIRDA nima ish qilayotgani va joriy joylashuvini aniqlash.
    """
    cache_key = f"live:{child_id}"
    cached = analytics_cache.get(cache_key)
    if cached:
        return cached

    conn = get_db()
    cursor = conn.cursor()

    # 1. Oxirgi navigatsiya (qaysi bo'limda)
    cursor.execute(
        """
        SELECT section_key, section_name, action_type, created_at 
        FROM child_navigation_logs 
        WHERE child_id = ? 
        ORDER BY id DESC LIMIT 1
        """,
        (child_id,)
    )
    last_nav = cursor.fetchone()

    # 2. Oxirgi AI chat
    cursor.execute(
        """
        SELECT role, message, planet_name, created_at 
        FROM ai_chat_history 
        WHERE child_id = ? 
        ORDER BY id DESC LIMIT 1
        """,
        (child_id,)
    )
    last_chat = cursor.fetchone()

    # 3. Oxirgi o'rganilgan ingliz tili so'zi (Uran)
    cursor.execute(
        """
        SELECT w.word_uz, w.word_en, l.last_learned_at 
        FROM child_uran_learned_words l
        JOIN uran_words w ON l.word_id = w.id
        WHERE l.child_id = ? 
        ORDER BY l.id DESC LIMIT 1
        """,
        (child_id,)
    )
    last_word = cursor.fetchone()

    # 4. Oxirgi o'qilgan kitob (Kutubxona)
    cursor.execute(
        """
        SELECT b.title, p.last_listened_at 
        FROM library_book_progress p
        JOIN library_books b ON p.book_id = b.id
        WHERE p.child_id = ? 
        ORDER BY p.id DESC LIMIT 1
        """,
        (child_id,)
    )
    last_book = cursor.fetchone()

    # 5. Oxirgi emotsiya / kayfiyat
    cursor.execute(
        """
        SELECT emotion_name, emoji, date, time 
        FROM child_emotions 
        WHERE child_id = ? 
        ORDER BY id DESC LIMIT 1
        """,
        (child_id,)
    )
    last_emotion = cursor.fetchone()

    conn.close()

    # Hozirgi holatni matnli ifodalash (Human-readable summary)
    current_location = "Bosh sahifa"
    activity_summary = "Platformaga kirmoqda"
    status_time = None

    candidates = []
    if last_nav:
        candidates.append((last_nav["created_at"], f"{last_nav['section_name']} bo'limida ko'rib chiqmoqda", last_nav['section_name']))
    if last_chat:
        planet_str = f" ({last_chat['planet_name']} sayyorasi)" if last_chat['planet_name'] else ""
        candidates.append((last_chat["created_at"], f"Bilag'on AI bilan suhbatlashmoqda{planet_str}", last_chat['planet_name'] or "AI Suhbat"))
    if last_word:
        candidates.append((last_word["last_learned_at"], f"Uran sayyorasida '{last_word['word_en']}' ({last_word['word_uz']}) so'zini yodlamoqda", "Uran (Ingliz tili)"))
    if last_book:
        candidates.append((last_book["last_listened_at"], f"Kutubxonada '{last_book['title']}' ertagini tinglamoqda", "Kutubxona"))

    # Eng so'nggi harakatni tanlash
    if candidates:
        candidates.sort(key=lambda x: str(x[0]), reverse=True)
        status_time = candidates[0][0]
        activity_summary = candidates[0][1]
        current_location = candidates[0][2]

    mood_str = f"{last_emotion['emoji']} {last_emotion['emotion_name']}" if last_emotion else "A'lo 😊"

    out = {
        "current_location": current_location,
        "current_activity": activity_summary,
        "current_mood": mood_str,
        "last_active_at": status_time,
        "is_online_recently": True if status_time else False
    }
    analytics_cache.set(cache_key, out, ttl=30)
    return out

def get_child_full_analytics(child_id: int, days: int = 7) -> Dict[str, Any]:
    """
    Bolaning barcha bo'limlar bo'yicha to'liq statistikasi:
    - Qaysi bo'limlarda yuribdi
    - Ko'proq nimalar bilan shug'ullanayapti
    - O'rgangan bilimlari, yutuqlari va emotsiyalari
    """
    cache_key = f"analytics:{child_id}:{days}"
    cached = analytics_cache.get(cache_key)
    if cached:
        return cached

    profile = get_child_profile(child_id)
    if not profile:
        return {}

    conn = get_db()
    cursor = conn.cursor()

    # 1. Kunlik faollik va vaqt (child_activities)
    cursor.execute(
        """
        SELECT date, minutes_spent, messages_count, planet_id 
        FROM child_activities 
        WHERE child_id = ? 
        ORDER BY date DESC LIMIT ?
        """,
        (child_id, days)
    )
    act_rows = [dict(r) for r in cursor.fetchall()]

    total_minutes = sum(r["minutes_spent"] for r in act_rows)
    total_messages = sum(r["messages_count"] for r in act_rows)

    # 2. Navigatsiya bo'yicha bo'limlar taqsimoti (child_navigation_logs)
    cursor.execute(
        """
        SELECT section_name, COUNT(*) as visit_count 
        FROM child_navigation_logs 
        WHERE child_id = ? 
        GROUP BY section_name 
        ORDER BY visit_count DESC
        """,
        (child_id,)
    )
    nav_stats = [dict(r) for r in cursor.fetchall()]

    # Sayyoralar nomi bo'yicha xaritalash
    PLANET_NAMES = {
        42: "Kognitiv (Mantiq va Aql)",
        43: "Jismoniy va motorika",
        44: "Nutq va til (Ertaklar)",
        45: "Ijtimoiy (Do'stlik)",
        46: "Emotsional (Kayfiyat)",
        47: "Axloqiy (Odob-axloq)",
        48: "Ijodkorlik (San'at)",
        49: "O'z-o'zini boshqarish",
        50: "Quyosh (AI Markazi)"
    }

    # Sayyoralar bo'yicha daqiqalarni jamlash
    planet_minutes = {}
    for r in act_rows:
        pid = r.get("planet_id") or 42
        pname = PLANET_NAMES.get(pid, f"Sayyora #{pid}")
        planet_minutes[pname] = planet_minutes.get(pname, 0) + r["minutes_spent"]

    # Agar planet_minutes bo'sh bo'lsa nav_stats dan olamiz
    if not planet_minutes and nav_stats:
        for ns in nav_stats:
            planet_minutes[ns["section_name"]] = ns["visit_count"] * 3

    # Eng ko'p shug'ullanayotgan sohalar (Top Favorites)
    top_activities = sorted(planet_minutes.items(), key=lambda x: x[1], reverse=True)
    favorites_list = []
    for name, mins in top_activities[:4]:
        pct = round((mins / total_minutes * 100), 1) if total_minutes > 0 else 25.0
        favorites_list.append({"name": name, "minutes": mins, "percentage": pct})

    # 3. Uran (Ingliz tili) bilimlari
    cursor.execute(
        """
        SELECT COUNT(*) as total_learned,
               SUM(correct_count) as total_correct,
               SUM(wrong_count) as total_wrong 
        FROM child_uran_learned_words 
        WHERE child_id = ?
        """,
        (child_id,)
    )
    uran_stats = dict(cursor.fetchone())

    # 4. Kutubxona statistikasi
    cursor.execute(
        """
        SELECT COUNT(*) as books_started,
               SUM(is_completed) as books_completed 
        FROM library_book_progress 
        WHERE child_id = ?
        """,
        (child_id,)
    )
    lib_stats = dict(cursor.fetchone())

    # 5. Emotsiyalar tahlili
    cursor.execute(
        """
        SELECT emotion_name, emoji, COUNT(*) as cnt 
        FROM child_emotions 
        WHERE child_id = ? 
        GROUP BY emotion_name 
        ORDER BY cnt DESC
        """,
        (child_id,)
    )
    emotion_rows = [dict(r) for r in cursor.fetchall()]

    # 6. Tangalar va daraja
    cursor.execute("SELECT total_coins, streak_days, level FROM child_coins WHERE child_id = ?", (child_id,))
    coins_row = cursor.fetchone()
    coins_data = dict(coins_row) if coins_row else {"total_coins": 0, "streak_days": 1, "level": 1}

    # 7. Bolaning AI bilan oxirgi savollari va qiziqishlari
    cursor.execute(
        """
        SELECT message, created_at 
        FROM ai_chat_history 
        WHERE child_id = ? AND role = 'user' 
        ORDER BY id DESC LIMIT 5
        """,
        (child_id,)
    )
    recent_questions = [r["message"] for r in cursor.fetchall()]

    conn.close()

    live_status = get_child_live_status(child_id)

    result = {
        "child_id": child_id,
        "name": profile["name"],
        "surname": profile["surname"],
        "age": profile["age"],
        "gender": profile["gender_clean"],
        "live_status": live_status,
        "screen_time": {
            "total_minutes_last_7_days": total_minutes,
            "total_ai_messages": total_messages,
            "daily_records": act_rows
        },
        "most_active_sections": favorites_list,
        "learning_progress": {
            "uran_english_words_learned": uran_stats.get("total_learned") or 0,
            "uran_correct_answers": uran_stats.get("total_correct") or 0,
            "uran_wrong_answers": uran_stats.get("total_wrong") or 0,
            "library_books_listened": lib_stats.get("books_started") or 0,
            "library_books_completed": lib_stats.get("books_completed") or 0,
            "coins": coins_data.get("total_coins", 0),
            "level": coins_data.get("level", 1)
        },
        "emotions_summary": emotion_rows,
        "recent_interests_and_questions": recent_questions
    }

    analytics_cache.set(cache_key, result, ttl=45)
    return result
