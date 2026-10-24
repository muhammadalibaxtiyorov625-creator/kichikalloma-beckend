import os
from dotenv import load_dotenv

# .env faylini yuklash (asosiy backend papkasidan)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path, override=True)
else:
    load_dotenv(override=True)

# LLM API Kalitlari
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("GOOGLE_API_KEY", "").strip()

# Ovoz (Edge-TTS) sozlamalari
VOICE_NAME_UZ = os.getenv("VOICE_NAME_UZ", "uz-UZ-MadinaNeural").strip()
VOICE_NAME_RU = os.getenv("VOICE_NAME_RU", "ru-RU-SvetlanaNeural").strip()
VOICE_NAME_EN = os.getenv("VOICE_NAME_EN", "en-US-JennyNeural").strip()

# Kesh va yuklama sozlamalari
CACHE_TTL_SECONDS = 60
REQUEST_TIMEOUT_SECONDS = 12.0
