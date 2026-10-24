from .config import GROQ_API_KEY, ANTHROPIC_API_KEY, CLAUDE_MODEL, GEMINI_API_KEY
from .web_search import search_google_web, async_search_google, is_search_needed
from .smart_tutor import is_math_question, solve_math
from .voice_service import generate_speech_base64, clean_for_speech, detect_language
from .prompts import build_adaptive_system_prompt
from .llm_engine import generate_llm_response
from .child_intelligence import (
    get_child_profile,
    get_child_live_status,
    get_child_full_analytics,
    track_child_navigation
)
from .parent_advisor import generate_parent_report, answer_parent_query

__all__ = [
    "GROQ_API_KEY",
    "ANTHROPIC_API_KEY",
    "CLAUDE_MODEL",
    "GEMINI_API_KEY",
    "search_google_web",
    "async_search_google",
    "is_search_needed",
    "is_math_question",
    "solve_math",
    "generate_speech_base64",
    "clean_for_speech",
    "detect_language",
    "build_adaptive_system_prompt",
    "generate_llm_response",
    "get_child_profile",
    "get_child_live_status",
    "get_child_full_analytics",
    "track_child_navigation",
    "generate_parent_report",
    "answer_parent_query"
]
