import asyncio
import edge_tts
import os
import re
import hashlib

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

async def pregenerate_all_planet_audios():
    os.makedirs('public/audio_cache', exist_ok=True)
    for pid, intro in PLANET_INTROS_STATIC.items():
        clean = re.sub(r'[*#_`~>•]', '', intro)
        clean = re.sub(r'[\U00010000-\U0010ffff]', '', clean).strip()
        hash_key = hashlib.md5(f"uz-UZ-SardorNeural:+32Hz:+8%:+50%:{clean}".encode('utf-8')).hexdigest()
        file_path = os.path.join('public/audio_cache', f'{hash_key}.mp3')
        if not os.path.exists(file_path):
            c = edge_tts.Communicate(clean, 'uz-UZ-SardorNeural', pitch='+32Hz', rate='+8%', volume='+50%')
            await c.save(file_path)
            print(f"Sayyora {pid} audio yaratildi: {file_path}")
        else:
            print(f"Sayyora {pid} audio mavjud: {file_path}")

if __name__ == '__main__':
    asyncio.run(pregenerate_all_planet_audios())
