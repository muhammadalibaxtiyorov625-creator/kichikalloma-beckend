# -*- coding: utf-8 -*-
"""
========================================================================================
🚀 KICHIK ALLOMA — TELEGRAM BOT (AI YORDAMCHI)
========================================================================================
Ushbu bot:
1. Kichik Alloma Backend API (http://127.0.0.1:3000/api/website/ai/chat) ga ulanadi.
   - Backend orqali barcha fanlar, jonli qidiruv va Microsoft Edge-TTS ovozli
     javoblari (Voice message) yuboriladi.
2. Google Gemini AI (gemini-2.5-flash / gemini-1.5-flash) zaxirasi bilan ta'minlangan.
3. Telegram botida bolalar uchun mo'ljallangan maxsus Kichik Alloma System Prompti
   to'liq joylashtirilgan.
========================================================================================
"""

import os
import re
import sys
import logging
import asyncio
import aiohttp
from typing import Optional

from aiogram import Bot, Dispatcher, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, BufferedInputFile

# Google Gemini import
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


# ======================================================================================
# 1. KONFIGURATSIYA (O'zingizning tokenlaringizni shu yerga kiriting)
# ======================================================================================
# Telegram BotFather dan olingan bot tokeni:
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "7942738734:AAElWqB-KvhqA671eL0-G6dYx5qY8l6Qx8o")

# Kichik Alloma Backend manzili:
BACKEND_BASE_URL = os.environ.get("BACKEND_BASE_URL", "http://127.0.0.1:3000")
BACKEND_CHAT_URL = f"{BACKEND_BASE_URL}/api/website/ai/chat"

# Google Gemini API kaliti:
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "") or os.environ.get("GOOGLE_API_KEY", "")
if GEMINI_API_KEY and GEMINI_AVAILABLE:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as e:
        logging.warning(f"Gemini configure xatosi: {e}")


# ======================================================================================
# 2. KICHIK ALLOMA — MAXSUS TIZIM PROMTI (SYSTEM PROMPT)
# ======================================================================================
SYSTEM_PROMPT = """
Sen — "Alloma AI", ya'ni bolalar uchun mo'ljallangan "Kichik Alloma" interaktiv ta'lim platformasining eng aqlli, mehribon, quvnoq va do'stona virtual ustozi va do'stisan!

LOYIHA VA ASOSCHILAR HAQIDA MA'LUMOT (QAT'IY QOIDA):
- Agar sendan "Seni kim yaratgan?", "Kichik Allomani kim yaratgan?", "Founder kim?" yoki "Loyihani kim qilgan?" deb so'rashsa, har doim quyidagicha javob ber:
  "Meni va Kichik Alloma loyihasini faqat bir kishi emas, balki bizning asoschimiz (founderimiz) — Shoxrux Komiljonov va uning ahil, iqtidorli jamoasi birgalikda yaratgan! 🚀✨ Bizning jamoamiz bolajonlar har kuni yangi bilimlarni qiziqarli, oson va quvnoq o'rganishlari uchun meni katta mehr bilan ishlab chiqishgan. Siz bilan do'st bo'lib, yangi marralarni zabt etishdan judayam baxtiyormiz! 🌟"

ISM ISHLATISHNING QAT'IY QOIDASI:
- Hech qachon to'qima yoki begona ismlarni (masalan, "Temur", "Madina" va h.k.) ishlatma!
- Bolaga samimiy tarzda "do'stim", "kichkintoy", "aziz do'stim" deb yoki to'g'ridan-to'g'ri murojaat qil.

PEDAGOGIK USLUB VA VAZIFALAR:
1. Savollarga aniq, mantiqiy, to'liq va bolalar tushunadigan tilda javob ber.
2. Fanlar bo'yicha:
   - Matematika: Amallarni (qo'shish, ayirish, ko'paytirish, bo'lish, ildiz, kvadrat) oson tushuntirib, to'g'ri hisoblab ber.
   - Koinot va Astronomiya: Quyosh, Oy, sayyoralar, yulduzlar va koinot sirlari haqida qiziqarli faktlar so'zla.
   - Biologiya va Tabiat: Hayvonlar (delfinlar qanday uxlaydi, chumolilar kuchi, gepard tezligi), inson tanasi (yurak, qon aylanishi, bosh miya) haqida ajoyib misollar keltir.
   - Fizika va Texnologiya: Nega osmon moviy, yomg'ir qanday yog'adi, samolyot nega uchadi, kompyuter va sun'iy intellekt qanday ishlaydi — sodda o'xshatishlar bilan tushuntir.
   - Ingliz tili: Agar bola inglizcha so'z so'rasa, so'zning ma'nosini, to'g'ri talaffuzini va qiziqarli misollarni ko'rsat.
3. Muloqot tili:
   - Bola o'zbekcha yozsa — sof, chiroyli va tushunarli o'zbek tilida javob ber.
   - Bola ruscha yozsa — bolalar uchun mos, chiroyli rus tilida javob ber.
   - Bola inglizcha yozsa — do'stona, sodda Amerika ingliz tilida javob ber.
4. Xarakter: Har doim dalda beruvchi, mehrli, rag'batlantiruvchi va quvnoq bo'l (emojilardan chiroyli foydalan: 🌟, 🚀, 💡, 🧠, 📚, ✨).
"""


# ======================================================================================
# 3. BACKEND VA GEMINI BILAN BOG'LANISH FUNKSIYALARI
# ======================================================================================

async def fetch_from_kichikalloma_backend(user_text: str, lang: str = "uzb") -> Optional[dict]:
    """
    Kichik Alloma FastAPI backendiga so'rov yuborish.
    Muvaffaqiyatli bo'lsa: {"text": str, "audio_url": Optional[str], "model": str} qaytaradi.
    """
    payload = {
        "message": user_text,
        "language": lang,
        "child_id": 1,
        "child_age": 8,
        "child_gender": "male"
    }
    timeout = aiohttp.ClientTimeout(total=8.0)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(BACKEND_CHAT_URL, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    response_text = data.get("response", "").strip()
                    audio_url = data.get("audio_url")
                    model_used = data.get("model_used", "kichikalloma-backend")
                    
                    if audio_url and not audio_url.startswith("http"):
                        # Nisbiy URL bo'lsa to'liq URLga aylantirish
                        audio_url = f"{BACKEND_BASE_URL.rstrip('/')}/{audio_url.lstrip('/')}"
                        
                    return {
                        "text": response_text,
                        "audio_url": audio_url,
                        "model": model_used
                    }
                else:
                    logging.warning(f"Backend status error: {resp.status}")
    except Exception as e:
        logging.info(f"Backend ulanishida xatolik (Gemini zaxirasiga o'tiladi): {e}")
    return None


async def fetch_audio_bytes(audio_url: str) -> Optional[bytes]:
    """Audio faylni bot serveridan yuklab olish (Telegramga ovozli xabar qilib jo'natish uchun)"""
    try:
        timeout = aiohttp.ClientTimeout(total=6.0)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(audio_url) as resp:
                if resp.status == 200:
                    return await resp.read()
    except Exception as e:
        logging.warning(f"Audio yuklab olishda xato: {e}")
    return None


async def fetch_from_direct_gemini(user_text: str) -> str:
    """
    Backend ulanmaganda to'g'ridan-to'g'ri Google Gemini AI dan javob olish
    """
    if not GEMINI_API_KEY or not GEMINI_AVAILABLE:
        return (
            "Salom, do'stim! 🌟 Men Kichik Alloma AI yordamchisiman. "
            "Hozirda savolingizga javob tayyorlashda tizimda yangilanish bormoqda. "
            "Birozdan so'ng yana qayta yozib ko'ring! 🚀"
        )

    try:
        # Eng yangi va tezkor Gemini modellari
        model_name = "gemini-2.5-flash"
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=SYSTEM_PROMPT,
                generation_config={"temperature": 0.7, "max_output_tokens": 800}
            )
            response = await asyncio.to_thread(model.generate_content, user_text)
            if response and response.text:
                return response.text.strip().replace("**", "").replace("##", "").replace("*", "•")
        except Exception:
            # Agar 2.5-flash bo'lmasa, 1.5-flash ni sinab ko'ramiz
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=SYSTEM_PROMPT,
                generation_config={"temperature": 0.7, "max_output_tokens": 800}
            )
            response = await asyncio.to_thread(model.generate_content, user_text)
            if response and response.text:
                return response.text.strip().replace("**", "").replace("##", "").replace("*", "•")
    except Exception as e:
        logging.error(f"Gemini API xatoligi: {e}")

    return "Ajoyib savol, do'stim! Keling, birgalikda yangi bilimlarni kashf etishda davom etamiz! 🌟"


# ======================================================================================
# 4. AIOGRAM TELEGRAM BOT HANDLERLARI
# ======================================================================================

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
bot = Bot(token=TELEGRAM_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: Message):
    """Start komandasi — bolajonlarni do'stona kutib olish"""
    welcome_text = (
        "<b>Salom, aziz do'stim!</b> 🚀✨\n\n"
        "Men — <b>Alloma AI</b>man! Bolajonlar uchun mo'ljallangan "
        "<b>Kichik Alloma</b> intellektual ta'lim platformasining do'stona yordamchisiman.\n\n"
        "Men bilan:\n"
        "• 🧠 <b>Matematika</b> — misol va jumboqlarni yechishingiz mumkin\n"
        "• 🪐 <b>Koinot va Tabiat</b> — sayyoralar, yulduzlar va hayvonot olami sirlarini bilib olasiz\n"
        "• 🇬🇧 <b>Ingliz tili</b> — yangi so'zlar va talaffuzni o'rganishingiz mumkin\n"
        "• 🎙️ <b>Ovozli javoblar</b> — har bir savolingizga jonli ovozda javob tinglashingiz mumkin!\n\n"
        "Menga xohlagan savolingizni yozing, birgalikda o'rganamiz! 😊🌟"
    )
    await message.answer(welcome_text)


@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Yordam komandasi"""
    help_text = (
        "💡 <b>Qanday savollar berishingiz mumkin?</b>\n\n"
        "1. <i>'Seni kim yaratgan?'</i> — Loyiha va asoschilar haqida bilish\n"
        "2. <i>'Delfinlar qanday uxlaydi?'</i> — Qiziqarli tabiat faktlari\n"
        "3. <i>'Samolyot qanday uchadi?'</i> — Fizika va texnika mo'jizalari\n"
        "4. <i>'25 ning kvadrati nechchi?'</i> — Tezkor hisob-kitoblar\n"
        "5. <i>'Olma inglizchasiga nima bo'ladi?'</i> — Ingliz tili saboqlari\n\n"
        "Savolingizni shunchaki matn ko'rinishida yuboring! 🚀"
    )
    await message.answer(help_text)


@dp.message(F.text)
async def handle_text_message(message: Message):
    """Foydalanuvchi yuborgan barcha matnli savollarni qabul qilish va javob berish"""
    user_text = message.text.strip()
    if not user_text:
        return

    # Foydalanuvchiga javob tayyorlanayotganini bildirish (Typing indikatori)
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    ai_reply_text = None
    audio_bytes = None

    # 1-QADAM: Kichik Alloma backendiga so'rov yuborish
    backend_result = await fetch_from_kichikalloma_backend(user_text)

    if backend_result and backend_result.get("text"):
        ai_reply_text = backend_result["text"]
        audio_url = backend_result.get("audio_url")
        
        # Agar backend ovozli audio URL qaytargan bo'lsa, uni yuklab olamiz
        if audio_url:
            audio_bytes = await fetch_audio_bytes(audio_url)
    else:
        # 2-QADAM: Backend offline bo'lsa, to'g'ridan-to'g'ri Gemini AI ga murojaat
        ai_reply_text = await fetch_from_direct_gemini(user_text)

    # 3-QADAM: Matnli javobni yuborish
    if ai_reply_text:
        await message.answer(ai_reply_text, parse_mode=None)

    # 4-QADAM: Ovozli xabar (Voice) mavjud bo'lsa, uni yuborish
    if audio_bytes:
        try:
            await bot.send_chat_action(chat_id=message.chat.id, action="record_voice")
            voice_file = BufferedInputFile(audio_bytes, filename="alloma_voice.mp3")
            await message.answer_voice(voice=voice_file, caption="🎙️ Alloma AI ovozi ✨")
        except Exception as e:
            logging.warning(f"Voice jo'natishda xato: {e}")


@dp.message(F.voice)
async def handle_voice_message(message: Message):
    """Ovozli xabar yuborilganda javob berish"""
    await message.reply(
        "Ajoyib ovozli xabar! 🎙️ Hozircha menga savollaringizni matn ko'rinishida yozsangiz, "
        "men sizga ham matnda, ham chiroyli ovozda javob qaytaraman! 😊✨"
    )


# ======================================================================================
# 5. ASOSIY ISHGA TUSHIRISH SIKLI (MAIN)
# ======================================================================================
async def main():
    print("=" * 60)
    print("🚀 Kichik Alloma Telegram Boti ishga tushmoqda...")
    print(f"📡 Backend URL: {BACKEND_CHAT_URL}")
    print(f"🤖 Gemini AI holati: {'Ulangan' if GEMINI_API_KEY else 'API kalit kiritilmagan'}")
    print("=" * 60)
    
    # Eski keshdagi yangilanishlarni tashlab yuborish va botni tinglashga qo'yish
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\nBot to'xtatildi.")
