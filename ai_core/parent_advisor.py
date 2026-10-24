from typing import Dict, Any, Optional
from .child_intelligence import get_child_full_analytics, get_child_profile
from .llm_engine import generate_llm_response

async def generate_parent_report(child_id: int) -> Dict[str, Any]:
    """
    Ota-ona uchun bolaning holati, nimalar bilan shug'ullanayotgani va
    pedagogik tavsiyalar bo'yicha sun'iy intellekt xulosasini tayyorlaydi.
    """
    analytics = get_child_full_analytics(child_id)
    if not analytics:
        return {"status": "error", "message": "Farzand ma'lumotlari topilmadi"}

    name = analytics.get("name", "Farzandingiz")
    age = analytics.get("age", 7)
    gender_str = "o'g'lingiz" if analytics.get("gender") == "boy" else "qizingiz"
    live = analytics.get("live_status", {})
    favorites = analytics.get("most_active_sections", [])
    learning = analytics.get("learning_progress", {})
    emotions = analytics.get("emotions_summary", [])
    recent_q = analytics.get("recent_interests_and_questions", [])

    fav_str = ", ".join([f"{f['name']} ({f['percentage']}%)" for f in favorites]) if favorites else "Boshlang'ich tanishuv"
    mood_str = emotions[0]["emotion_name"] if emotions else "Ijobiy va quvnoq"

    prompt = f"""Sen bolalar psixologi va professional pedagog maslahatchisisan.
Quyida ota-onaning {gender_str} {name} ({age} yosh) haqidagi platforma ma'lumotlar bazasi ko'rsatilgan:

1. HOZIRGI HOLATI:
   - Hozirgi joylashuvi: {live.get('current_location')}
   - Nima bilan shug'ullanmoqda: {live.get('current_activity')}
   - Kayfiyati: {live.get('current_mood')}

2. FAOLLIGI VA QIZIQISHLARI:
   - Eng ko'p vaqt o'tkazgan bo'limlari: {fav_str}
   - Oxirgi 7 kunda sarflagan vaqti: {analytics.get('screen_time', {}).get('total_minutes_last_7_days', 0)} daqiqa
   - AI bilan suhbatlashgan mavzulari va savollari: {', '.join(recent_q[:4]) if recent_q else 'Turli aqliy jumboqlar'}

3. O'ZLASHTIRISH NATIJALARI:
   - Yodlangan inglizcha so'zlar: {learning.get('uran_english_words_learned', 0)} ta
   - Tinglangan audio ertaklar: {learning.get('library_books_listened', 0)} ta
   - Jamg'argan bilimlari va tangalari: {learning.get('coins', 0)} Alloma tangasi

VAZIFA:
Ota-onaga tushunarli, dalda beruvchi, samimiy va professional tilda quyidagilarni o'z ichiga olgan hisobot yozib ber:
1. Bolaning hozirgi umumiy holati va nimalar bilan ko'proq shug'ullanayotgani.
2. Qaysi sohalarda kuchli rivojlanayotgani (yutuqlari).
3. Qaysi yo'nalishlarga ko'proq e'tibor qaratish kerakligi.
4. Ota-onaga uyda {name} bilan muloqot qilish bo'yicha 2 ta aniq va amaliy tavsiya.
Javobing 3-4 ta chiroyli abzasda bo'lsin. Hech qanday yulduzcha (*) yoki maxsus belgilar ishlatma.
"""

    messages = [{"role": "user", "content": f"{name} haqida to'liq xulosa va tavsiyalar ber"}]
    ai_summary, model_used = await generate_llm_response(messages, prompt, child_name=name)

    return {
        "status": "success",
        "child_id": child_id,
        "child_name": name,
        "age": age,
        "gender": analytics.get("gender"),
        "live_status": live,
        "analytics_data": analytics,
        "ai_parent_insight": ai_summary,
        "model_used": model_used
    }

async def answer_parent_query(child_id: int, parent_question: str) -> Dict[str, Any]:
    """
    Ota-onaning bolasi haqidagi istalgan savoliga bazadagi ma'lumotlar asosida javob berish.
    (Masalan: "Bolam bugun nimalar qildi?", "Hozir qayerda yuribdi?", "Kayfiyati qanday?")
    """
    analytics = get_child_full_analytics(child_id)
    if not analytics:
        return {
            "status": "error",
            "message": "Farzand ma'lumotlari topilmadi"
        }

    name = analytics.get("name", "Farzandingiz")
    age = analytics.get("age", 7)
    gender_str = "o'g'lingiz" if analytics.get("gender") == "boy" else "qizingiz"
    live = analytics.get("live_status", {})
    favorites = analytics.get("most_active_sections", [])
    learning = analytics.get("learning_progress", {})
    recent_q = analytics.get("recent_interests_and_questions", [])

    system_prompt = f"""Sen ota-onaga uning farzandi haqida to'liq ma'lumot beruvchi mehribon, pedagog AI yordamchisan.
OTA-ONANING FARZANDI HAQIDAGI ANIQ MA'LUMOTLAR BAZASI:
- Ismi: {name}
- Yoshi: {age} yosh
- Jinsi: {gender_str}
- Hozirgi joylashuvi (bo'lim): {live.get('current_location')}
- Hozirda qilayotgan ishi: {live.get('current_activity')}
- Hozirgi kayfiyati: {live.get('current_mood')}
- Eng ko'p kirgan bo'limlari: {', '.join([f['name'] for f in favorites]) if favorites else 'Kognitiv sayyora'}
- O'rgangan inglizcha so'zlari: {learning.get('uran_english_words_learned', 0)} ta
- Tinglagan kitoblari: {learning.get('library_books_listened', 0)} ta
- AI bilan so'ragan savollari: {', '.join(recent_q) if recent_q else 'Tabiat va kosmos haqida'}

OTA-ONA SAVOLI: "{parent_question}"

KO'RSATMA:
- Ota-onaning savoliga aynan yuqoridagi bazaviy ma'lumotlarga tayangan holda to'liq va aniq javob ber!
- Agar bola hozir nima ish qilayotganini so'rasa, uning joriy joylashuvi va oxirgi faolligini aytib ber.
- Agar qiziqishlarini so'rasa, ko'proq qaysi sayyoralarda yurganini tushuntir.
- Javobing juda samimiy, xushmuomala, ota-onaga dalda beruvchi va aniq faktlarga asoslangan bo'lsin.
- Maxsus belgilar (*, #, _) ishlatma.
"""

    messages = [{"role": "user", "content": parent_question}]
    answer, model_used = await generate_llm_response(messages, system_prompt, child_name=name)

    return {
        "status": "success",
        "child_id": child_id,
        "child_name": name,
        "parent_question": parent_question,
        "ai_answer": answer,
        "live_status": live,
        "model_used": model_used
    }
