import os
import re
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Request, Depends, UploadFile, File, Form
from pydantic import BaseModel

from ai_core.child_intelligence import (
    get_child_profile,
    get_child_live_status,
    get_db
)
from ai_core.prompts import build_adaptive_system_prompt
from ai_core.smart_tutor import is_math_question, solve_math
from ai_core.web_search import is_search_needed, async_search_google
from ai_core.llm_engine import generate_llm_response
from ai_core.voice_service import generate_speech_base64, clean_for_speech, detect_language

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChildChatRequest(BaseModel):
    message: str
    child_id: Optional[int] = None
    user_id: Optional[int] = None
    planet_id: Optional[int] = None
    planet_name: Optional[str] = None
    language: Optional[str] = "uz"
    history: Optional[List[ChatMessage]] = []

def save_interaction(user_id: Optional[int], child_id: Optional[int], user_msg: str, ai_text: str, planet_id: Optional[int], planet_name: Optional[str]):
    """Suhbat va faollikni bazaga asinxron/xavfsiz yozish"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # 1. AI Chat History
        cursor.execute(
            """
            INSERT INTO ai_chat_history (user_id, child_id, role, message, planet_id, planet_name)
            VALUES (?, ?, 'user', ?, ?, ?)
            """,
            (user_id or 1, child_id, user_msg, planet_id, planet_name)
        )
        cursor.execute(
            """
            INSERT INTO ai_chat_history (user_id, child_id, role, message, planet_id, planet_name)
            VALUES (?, ?, 'model', ?, ?, ?)
            """,
            (user_id or 1, child_id, ai_text, planet_id, planet_name)
        )

        # 2. child_activities yangilash
        if child_id:
            from datetime import datetime
            today_str = datetime.now().strftime("%Y-%m-%d")
            t_planet = planet_id or 50
            cursor.execute(
                "SELECT id FROM child_activities WHERE child_id = ? AND date = ? AND planet_id = ?",
                (child_id, today_str, t_planet)
            )
            row = cursor.fetchone()
            if row:
                cursor.execute(
                    "UPDATE child_activities SET minutes_spent = minutes_spent + 2, messages_count = messages_count + 1 WHERE id = ?",
                    (row["id"],)
                )
            else:
                cursor.execute(
                    "INSERT INTO child_activities (user_id, child_id, date, minutes_spent, messages_count, planet_id) VALUES (?, ?, ?, 2, 1, ?)",
                    (user_id or 1, child_id, today_str, t_planet)
                )

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Save Interaction Error]: {e}")

@router.post("/chat", summary="Bolaning yoshi va jinsiga avtomatik moslashuvchi AI suhbat")
async def child_ai_chat(req: ChildChatRequest, request: Request):
    user_msg = req.message.strip()
    if not user_msg:
        raise HTTPException(status_code=400, detail="Xabar bo'sh bo'lishi mumkin emas")

    # 1. Bolaning profilini bazadan aniqlash
    child_id = req.child_id
    child_profile = None
    if child_id:
        child_profile = get_child_profile(child_id)

    child_name = child_profile["name"] if child_profile else "bolajon"
    age = child_profile["age"] if child_profile else 7
    gender = child_profile["gender_clean"] if child_profile else "male"
    user_id = req.user_id or (child_profile["user_id"] if child_profile else 1)

    # 2. Bolaning joriy holatini olish
    live_status = get_child_live_status(child_id) if child_id else {}
    current_location = req.planet_name or live_status.get("current_location", "Kichik Alloma")
    current_act = live_status.get("current_activity", "Faol muloqot")

    # 3. Matematik savollarni 100% aniq va pedagogik yechish
    if is_math_question(user_msg):
        math_ans = solve_math(user_msg, child_name=child_name, age=age)
        if math_ans:
            audio_b64 = await generate_speech_base64(math_ans, lang=req.language or "uz", age=age, gender=gender)
            save_interaction(user_id, child_id, user_msg, math_ans, req.planet_id, req.planet_name)
            return {
                "status": "success",
                "text": math_ans,
                "audio_base64": audio_b64,
                "child_id": child_id,
                "child_name": child_name,
                "adapted_age": age,
                "adapted_gender": gender,
                "model_used": "Alloma Matematik Daho",
                "google_searched": False
            }

    # 4. Moslashuvchan tizim promptini shakllantirish
    system_prompt = build_adaptive_system_prompt(
        child_name=child_name,
        age=age,
        gender=gender,
        current_location=current_location,
        live_activity=current_act
    )

    # 5. Jonli Google va YouTube qidiruvi (kinolar, musiqa, multfilmlar, saytlar)
    google_searched = False
    if is_search_needed(user_msg):
        search_res = await async_search_google(user_msg, max_results=4)
        if search_res:
            google_searched = True
            system_prompt += f"\n\nGOOGLE VA YOUTUBE DAN JONLI HAQIQIY MA'LUMOTLAR:\n\"\"\"{search_res}\"\"\"\nKo'rsatma: Bolaga mavzuni qiziqarli tushuntir va natijalardagi to'g'ri YouTube yoki veb-sayt linklarini taqdim et!"

    # 6. Suhbat tarixini shakllantirish
    formatted_messages = []
    if req.history:
        for h in req.history[-6:]:
            if h.role in ["user", "assistant", "model"] and h.content.strip():
                formatted_messages.append({
                    "role": "user" if h.role == "user" else "assistant",
                    "content": h.content.strip()
                })
    formatted_messages.append({"role": "user", "content": user_msg})

    # 7. Ko'p pog'onali LLM generatsiyasi (Groq -> Gemini -> Claude)
    reply_text, model_used = await generate_llm_response(formatted_messages, system_prompt, child_name=child_name)

    # Chat matnini tozalash (haqiqiy linklar saqlanadi)
    display_text = re.sub(r'[*#_`~>|]', '', reply_text).strip()

    # 8. Ovoz yaratish (Edge-TTS bolaning yoshiga mos pitch va rate bilan)
    detected_lang = detect_language(display_text)
    audio_b64 = await generate_speech_base64(display_text, lang=detected_lang, age=age, gender=gender)

    # 9. Baza qaydlarini yozish
    save_interaction(user_id, child_id, user_msg, display_text, req.planet_id, req.planet_name)

    return {
        "status": "success",
        "text": display_text,
        "audio_base64": audio_b64,
        "child_id": child_id,
        "child_name": child_name,
        "adapted_age": age,
        "adapted_gender": gender,
        "detected_language": detected_lang,
        "google_searched": google_searched,
        "model_used": model_used
    }
