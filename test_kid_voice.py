import asyncio
import edge_tts
import os

async def generate_kid_voices():
    text = "Salom! Men Alloma AI bo'laman! Qanday yordam bera olaman?"
    
    tests = [
        # (voice, pitch, rate, label)
        ("uz-UZ-SardorNeural", "+20Hz", "+6%", "sardor_20hz"),
        ("uz-UZ-SardorNeural", "+30Hz", "+8%", "sardor_30hz"),
        ("uz-UZ-SardorNeural", "+38Hz", "+10%", "sardor_38hz"),
        ("uz-UZ-MadinaNeural", "+15Hz", "+5%", "madina_15hz"),
        ("uz-UZ-MadinaNeural", "+25Hz", "+8%", "madina_25hz"),
    ]
    
    for voice, pitch, rate, label in tests:
        file_path = f"public/audio_cache/test_voice_{label}.mp3"
        c = edge_tts.Communicate(text, voice, pitch=pitch, rate=rate, volume="+50%")
        await c.save(file_path)
        print(f"Generated: {label} -> {file_path} ({os.path.getsize(file_path)} bytes)")

if __name__ == '__main__':
    asyncio.run(generate_kid_voices())
