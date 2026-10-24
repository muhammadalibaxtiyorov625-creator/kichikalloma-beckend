import os
import re
import base64
import asyncio
from typing import Optional
import edge_tts
from .config import VOICE_NAME_UZ, VOICE_NAME_RU, VOICE_NAME_EN

COMMON_EN_WORDS = {
    'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i', 'it', 'for', 'not', 'on', 'with',
    'he', 'as', 'you', 'do', 'at', 'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her',
    'she', 'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their', 'what', 'so', 'up',
    'out', 'if', 'about', 'who', 'get', 'which', 'go', 'me', 'when', 'make', 'can', 'like', 'time',
    'no', 'just', 'him', 'know', 'take', 'people', 'into', 'year', 'your', 'good', 'some', 'could',
    'them', 'see', 'other', 'than', 'then', 'now', 'look', 'only', 'come', 'its', 'over', 'think',
    'also', 'back', 'after', 'use', 'two', 'how', 'our', 'work', 'first', 'well', 'way', 'even',
    'new', 'want', 'because', 'any', 'these', 'give', 'day', 'most', 'us', 'hello', 'hi', 'hey',
    'welcome', 'friend', 'today', 'tomorrow', 'yesterday', 'please', 'thanks', 'thank', 'is', 'are',
    'am', 'was', 'were', 'been', 'cat', 'dog', 'apple', 'sun', 'star', 'book', 'boy', 'girl', 'play',
    'tell', 'story', 'speak', 'talk', 'english', 'yes', 'cool', 'fine', 'song', 'music', 'listen',
    'here', 'watch', 'video'
}

COMMON_UZ_WORDS = {
    'bu', 'va', 'bilan', 'uchun', 'ham', 'emas', 'kerak', 'bor', 'yoq', 'yoki',
    'juda', 'katta', 'kichik', 'bolalar', 'bolajon', 'ustoz', 'salom', 'rahmat', 'albatta',
    'mana', 'ha', 'shunday', 'men', 'sen', 'biz', 'siz', 'ular', 'qanday', 'nima', 'qayerda',
    'qachon', 'chunki', 'shuning', 'qilish', 'boladi', 'edi', 'ekan', 'deb', 'ushbu', 'sayt',
    'havola', 'qoshiq', 'musiqa', 'eshitish', 'mumkin', 'videoni', 'tomosha', 'qiling', 'topdim',
    'havolasi', 'orqali', 'tinglashingiz', 'kino', 'film', 'multfilm'
}

def detect_language(text: str) -> str:
    """Matn tilini aniqlaydi: 'en', 'uz', 'ru'."""
    t_clean = re.sub(r'https?://[^\s]+', '', text)
    t_lower = t_clean.lower()

    uz_requests = [
        'ozbekcha', "o'zbekcha", 'uzbekcha', 'uzb', 'tarjima', 'tarjima qil',
        'ozbek tiliga', "o'zbek tiliga", 'ozbekchaga', "o'zbekchaga",
        'ozbekchasini', "o'zbekchasini", "o'zbek tilida", "ozbek tilida",
        'endi buni ozbekcha', "endi buni o'zbekcha", 'endi ozbekcha', "endi o'zbekcha"
    ]
    if any(p in t_lower for p in uz_requests):
        return 'uz'

    if any(p in t_lower for p in ['inglizcha gapir', 'inglizcha gaplash', 'ingliz tilida gapir', 'speak english', 'in english', 'say in english']):
        return 'en'

    cyrillic_chars = len(re.findall(r'[\u0400-\u04FF]', t_clean))
    if cyrillic_chars > len(t_clean) * 0.3 and len(t_clean) > 5:
        return 'ru'

    words = re.findall(r'[a-zA-Z]+', t_lower)
    if not words:
        return 'uz'

    uz_matches = sum(1 for w in words if w in COMMON_UZ_WORDS)
    en_matches = sum(1 for w in words if w in COMMON_EN_WORDS)

    if uz_matches > en_matches:
        return 'uz'
    if en_matches > uz_matches and (en_matches >= 2 or len(words) <= 3):
        return 'en'
    if en_matches / len(words) >= 0.3:
        return 'en'

    return 'uz'

def clean_for_speech(text: str) -> str:
    """Ovozli nutq (Edge-TTS) uchun belgilarni va URL larni ravon qiladi."""
    if not text:
        return ""
    # URL larni talaffuzda ravon qilish: "https://..." -> "ushbu havola orqali"
    clean = re.sub(r'https?://[^\s]+', 'ushbu havola orqali', text)
    clean = re.sub(r'[*#_`~>|]', '', clean)
    clean = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean)
    clean = re.compile('[\U00010000-\U0010ffff]', flags=re.UNICODE).sub('', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean

def get_voice_params_for_child(age: int = 7, gender: str = "male") -> tuple[str, str]:
    """Tabiiy, toza va jarangdor ovoz parametrlari."""
    return "+0Hz", "+0%"

async def generate_speech_base64(text: str, lang: str = "uz", age: int = 7, gender: str = "male") -> str:
    """
    Edge-TTS yordamida bolaning yoshi va tiliga moslashtirilgan audio yaratadi.
    """
    clean_text = clean_for_speech(text)
    if not clean_text:
        return ""

    # Til bo'yicha ovoz tanlash
    detected = detect_language(clean_text)
    if detected == "en":
        voice = VOICE_NAME_EN
    elif detected == "ru":
        voice = VOICE_NAME_RU
    else:
        voice = VOICE_NAME_UZ

    pitch, rate = get_voice_params_for_child(age=age, gender=gender)

    try:
        communicate = edge_tts.Communicate(clean_text, voice, pitch=pitch, rate=rate)
        audio_bytes = bytearray()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_bytes.extend(chunk["data"])

        if len(audio_bytes) > 0:
            b64_str = base64.b64encode(audio_bytes).decode("utf-8")
            return f"data:audio/mp3;base64,{b64_str}"
    except Exception as e:
        print(f"Edge-TTS xatosi ({voice}): {e}")

    return ""
