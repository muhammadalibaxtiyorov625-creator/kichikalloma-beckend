import asyncio
import urllib.parse
import re
from typing import Optional, List, Dict
import httpx
from ddgs import DDGS
from .smart_tutor import is_math_question, solve_math

def is_search_needed(query: str) -> bool:
    """Oddiy salomlashish va hisob-kitoblar uchun qidiruv kerak emas."""
    q = query.lower().strip()
    if len(q) < 4:
        return False
    # Matematik hisoblar bo'lsa, Google qidiruvi kerak emas
    if is_math_question(query) or solve_math(query):
        return False
    # Salomlashish va oddiy gaplar
    greetings = ["salom", "qalaysan", "qalesan", "nima gap", "rahmat", "xayr", "tuzikmisan", "isming nima", "kimsen", "hello", "hi", "how are you"]
    if any(q == g or q.startswith(g + " ") for g in greetings):
        return False
    # Oddiy arifmetika
    if re.search(r'^\s*\d+\s*[\+\-\*\/xX×÷]\s*\d+\s*$', q):
        return False
    return True

import asyncio
import urllib.parse
import re
from typing import Optional, List, Dict
import httpx
from ddgs import DDGS
from .smart_tutor import is_math_question, solve_math

def is_search_needed(query: str) -> bool:
    """Oddiy salomlashish va hisob-kitoblar uchun qidiruv kerak emas."""
    q = query.lower().strip()
    if len(q) < 4:
        return False
    # Matematik hisoblar bo'lsa, Google qidiruvi kerak emas
    if is_math_question(query) or solve_math(query):
        return False
    # Salomlashish va oddiy gaplar
    greetings = ["salom", "qalaysan", "qalesan", "nima gap", "rahmat", "xayr", "tuzikmisan", "isming nima", "kimsen", "hello", "hi", "how are you"]
    if any(q == g or q.startswith(g + " ") for g in greetings):
        return False
    # Oddiy arifmetika
    if re.search(r'^\s*\d+\s*[\+\-\*\/xX×÷]\s*\d+\s*$', q):
        return False
    return True

import asyncio
import urllib.parse
import urllib.request
import json
import re
from typing import Optional, List, Dict
import httpx
from ddgs import DDGS
from .smart_tutor import is_math_question, solve_math

def is_search_needed(query: str) -> bool:
    """Oddiy salomlashish va hisob-kitoblar uchun qidiruv kerak emas."""
    q = query.lower().strip()
    if len(q) < 4:
        return False
    # Matematik hisoblar bo'lsa, Google qidiruvi kerak emas
    if is_math_question(query) or solve_math(query):
        return False
    # Salomlashish va oddiy gaplar
    greetings = ["salom", "qalaysan", "qalesan", "nima gap", "rahmat", "xayr", "tuzikmisan", "isming nima", "kimsen", "hello", "hi", "how are you"]
    if any(q == g or q.startswith(g + " ") for g in greetings):
        return False
    # Oddiy arifmetika
    if re.search(r'^\s*\d+\s*[\+\-\*\/xX×÷]\s*\d+\s*$', q):
        return False
    return True

def clean_search_query(q: str) -> str:
    """Qidiruv tizimlari (DDGS/Google) operatorlarini va maxsus belgilarni tozalash."""
    # '-' belgisi DDGSda inkor (NOT) deb tushuniladi, shuning uchun bo'shliq bilan almashtiramiz
    cleaned = re.sub(r'[\-\–\—\_~#*`‘ʼ\'\"]+', ' ', q)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def search_wikipedia_fast(subject: str) -> list:
    """O'zbek, rus va ingliz Vikipediyasidan to'g'ridan-to'g'ri haqiqiy maqola havolalarini oladi."""
    if not subject or len(subject) < 2:
        return []
    for lang in ['uz', 'ru', 'en']:
        try:
            url = f"https://{lang}.wikipedia.org/w/api.php?action=opensearch&search={urllib.parse.quote(subject)}&limit=2&format=json"
            req = urllib.request.Request(url, headers={'User-Agent': 'AllomaAI/1.0'})
            with urllib.request.urlopen(req, timeout=2.5) as r:
                data = json.loads(r.read().decode('utf-8'))
                if data and len(data) >= 4 and data[1]:
                    return [{'title': data[1][i], 'url': data[3][i]} for i in range(len(data[1]))]
        except Exception:
            pass
    return []

def prepare_search_query(query: str) -> tuple[dict, list]:
    """
    Qidiruv so'rovini tahlil qiladi va mos qidiruv ketma-ketligini tuzadi.
    Kinolar, multfilmlar, seriallar, musiqa, Vikipediya va umumiy Google/YouTube so'rovlarini to'liq qo'llab-quvvatlaydi.
    """
    clean_q = clean_search_query(query)
    q_lower = clean_q.lower()

    movie_keywords = [
        'kino', 'kinolar', 'kinoni', 'kinolarni', 'kinosi', 'kinosini',
        'film', 'filmlar', 'filmni', 'filmlarni', 'filmi', 'filmini',
        'multfilm', 'multfilmlar', 'multfilmni', 'multfilmi', 'multfilmini', 'multik', 'multiklar',
        'serial', 'seriallar', 'serialni', 'seriali', 'serialini',
        'treyler', 'trailer', 'video', 'videolar', 'videoni',
        'movie', 'movies', 'cartoon', 'anime', 'cinema', 'mult'
    ]
    music_keywords = [
        'qoshiq', 'qoshigi', 'qoshigini', 'qoshiqni', 'musiqa', 'musiqasi', 'musiqani',
        'music', 'song', 'songs', 'klip', 'klipi', 'klipini', 'clip', 'mp3',
        'aytgan', 'ijrosida', 'ashula', 'ashulasi', 'ashulani'
    ]
    wiki_keywords = [
        'wiki', 'wikipedia', 'vikipediya', 'vikipedia', 'entsiklopediya', 'ensiklopediya'
    ]
    yt_keywords = [
        'youtube', 'yutub', 'youtubeda', 'yutubda', 'youtubedan', 'yutubdan'
    ]

    is_movie = any(k in q_lower for k in movie_keywords)
    is_music = any(k in q_lower for k in music_keywords)
    is_wiki = any(k in q_lower for k in wiki_keywords)
    is_youtube = any(k in q_lower for k in yt_keywords)
    is_media = is_movie or is_music or is_youtube

    # Buyruq va platforma so'zlarini tozalab, sof nomni ajratib olish
    stop_patterns = [
        r'\b(menga|bizga|shu|biror|biron|iltimos)\b',
        r'\b(topib\s+ber|izlab\s+ber|qidirib\s+ber|qidir\s+ber|qidirib\s+top|qidir|top|ko[\'\`‘ʼ]?rsat|korsat|ayt\s+ber|eshitaylik|tashla|ber)\b',
        r'\b(ko[\'\`‘ʼ]?rmoqchiman|kormoqchiman|tomosha\s+qilmoqchiman|eshitmoqchiman|tinglamoqchiman)\b',
        r'\b(haqida\s+ma[\'\`‘ʼ]?lumot\s+ber|haqida\s+gapir|haqida\s+aytib\s+ber|haqida|ma[\'\`‘ʼ]?lumot)\b',
        r'\b(linkini\s+ber|linkini\s+tashla|havolasini\s+ber|saytini\s+top|linkini|link|havola|saytini)\b',
        r'\b(kinosi|kinosini|kinoni|kino|filmi|filmini|filmni|film|multfilmi|multfilmini|multfilmni|multfilm|multik|seriali|serialini|serialni|serial)\b',
        r'\b(qoshigi|qoshigini|qoshiqni|qoshiq|musiqasi|musiqani|musiqa|ashulasi|ashulani|ashula)\b',
        r'\b(youtube|yutub|youtubeda|yutubda|youtubedan|yutubdan)\b',
        r'\b(wikipedia|vikipediya|vikipedia|wikipediyadan|vikipediyadan|wikipediada|vikipediyada)\b',
        r'\b(google|googledan|googleda)\b'
    ]
    subject = clean_q
    for pat in stop_patterns:
        subject = re.sub(pat, ' ', subject, flags=re.IGNORECASE)
    subject = re.sub(r'^(va|ham|bilan|da|dan|degan)\s+|\s+(va|ham|bilan|da|dan|degan)$', '', subject, flags=re.IGNORECASE)
    subject = re.sub(r'\s+', ' ', subject).strip()

    # Agar subject bo'sh qolsa (masalan: "menga youtube da qoshiq topib ber"):
    if not subject or len(subject) < 2 or subject.lower() in ['youtube', 'yutub', 'da', 'dan']:
        if is_music:
            subject = "bolalar qoshiqlari ozbek tilida"
        elif is_movie:
            subject = "bolalar uchun multfilmlar ozbek tilida"
        else:
            subject = clean_q

    # Qidiruv variantlari ketma-ketligi
    search_queries = []
    if is_media:
        if 'youtube' not in subject.lower():
            search_queries.append(f"{subject} youtube")
        search_queries.append(f"{subject} uzbek tilida")
        search_queries.append(subject)
    elif is_wiki:
        search_queries.append(f"{subject} wikipedia uz")
        search_queries.append(subject)
    else:
        search_queries.append(clean_q)
        if subject != clean_q:
            search_queries.append(subject)

    meta = {
        'subject': subject,
        'clean_query': clean_q,
        'is_movie': is_movie,
        'is_music': is_music,
        'is_wiki': is_wiki,
        'is_youtube': is_youtube,
        'is_media': is_media
    }
    return meta, search_queries

def search_google_web(query: str, max_results: int = 4) -> str:
    """Google, Vikipediya, YouTube va jonli internetdan aniq havolalar bilan ma'lumot oladi."""
    if not is_search_needed(query):
        return ""

    meta, search_queries = prepare_search_query(query)
    snippets = []
    subject = meta['subject']

    # 1. Agar Vikipediya so'ralgan bo'lsa yoki umumiy ensiklopedik savol bo'lsa
    wiki_articles = search_wikipedia_fast(subject)
    for w in wiki_articles:
        snippets.append(f"• Vikipediya Maqolasi: {w['title']}\n  Veb-sayt linki (URL): {w['url']}")

    # 2. DDGS orqali qidirish (ko'p bosqichli xavfsiz qidiruv)
    ddgs = DDGS(timeout=5)
    ddg_results = []
    for q_candidate in search_queries:
        try:
            res = list(ddgs.text(q_candidate, max_results=max_results))
            if res:
                ddg_results = res
                break
        except Exception:
            continue

    for r in ddg_results:
        body = r.get("body", "").strip()
        title = r.get("title", "").strip()
        href = r.get("href", "").strip().replace('https://m.youtube.com', 'https://www.youtube.com')
        if body or href:
            item_str = f"• Natija: {title}"
            if href:
                item_str += f"\n  Veb-sayt linki (URL): {href}"
            if body:
                item_str += f"\n  Ma'lumot: {body}"
            snippets.append(item_str)

    # 3. Agar kino, musiqa, video yoki youtube bo'lsa — YouTube qidiruv sahifasini qo'shamiz
    if meta['is_media'] and subject:
        yt_search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(subject)}"
        snippets.append(f"• YouTube to'g'ridan-to'g'ri qidiruv sahifasi: {yt_search_url}")

    # 4. Google to'g'ridan-to'g'ri qidiruv havolasi
    google_search_url = f"https://www.google.com/search?q={urllib.parse.quote(subject)}"
    snippets.append(f"• Google to'g'ridan-to'g'ri qidiruv havolasi: {google_search_url}")

    if snippets:
        return "\n\n".join(snippets[:max_results + 3])

    return ""

async def async_search_google(query: str, max_results: int = 3) -> str:
    """Asinxron qidiruv chaqiruvi."""
    try:
        return await asyncio.to_thread(search_google_web, query, max_results)
    except Exception as e:
        print(f"Asinxron Google qidiruv xatosi: {e}")
        return ""
