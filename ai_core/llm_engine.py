import os
import asyncio
from typing import List, Dict, Optional, Tuple
import httpx
from .config import GROQ_API_KEY, ANTHROPIC_API_KEY, CLAUDE_MODEL, GEMINI_API_KEY, REQUEST_TIMEOUT_SECONDS

# Doimiy qayta ishlatiladigan HTTP mijoz sessiyasi
_http_client: Optional[httpx.AsyncClient] = None

def get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        limits = httpx.Limits(max_keepalive_connections=50, max_connections=200)
        _http_client = httpx.AsyncClient(limits=limits, timeout=REQUEST_TIMEOUT_SECONDS)
    return _http_client

async def query_groq(messages: List[Dict[str, str]], system_prompt: str) -> Optional[str]:
    """Groq orqali ultra-tezkor va aniq javob olish (~300ms)."""
    if not GROQ_API_KEY:
        return None
    try:
        client = get_http_client()
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "KichikAllomaAI/2.0"
        }
        payload = {
            "model": "qwen/qwen3.8-27b",
            "messages": [{"role": "system", "content": system_prompt}] + messages,
            "max_tokens": 350,
            "temperature": 0.6
        }
        resp = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
        if resp.status_code == 200:
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[Groq LLM Error]: {e}")
    return None

async def query_gemini(messages: List[Dict[str, str]], system_prompt: str) -> Optional[str]:
    """Google Gemini 2.5 Flash orqali javob olish."""
    if not GEMINI_API_KEY:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=system_prompt)
        
        # Oxirgi savolni va tarixni tayyorlash
        history_contents = []
        for m in messages[:-1]:
            role = "user" if m["role"] == "user" else "model"
            history_contents.append({"role": role, "parts": [m["content"]]})
        
        chat = model.start_chat(history=history_contents)
        last_msg = messages[-1]["content"] if messages else "Salom"
        res = await asyncio.to_thread(chat.send_message, last_msg)
        if res and res.text:
            return res.text.strip()
    except Exception as e:
        print(f"[Gemini LLM Error]: {e}")
    return None

async def query_claude(messages: List[Dict[str, str]], system_prompt: str) -> Optional[str]:
    """Anthropic Claude 3.5 orqali javob olish."""
    if not ANTHROPIC_API_KEY or not ANTHROPIC_API_KEY.startswith("sk-ant-"):
        return None
    try:
        client = get_http_client()
        headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        claude_msgs = []
        for m in messages:
            if m["role"] in ["user", "assistant"]:
                claude_msgs.append({"role": m["role"], "content": m["content"]})
        
        payload = {
            "model": CLAUDE_MODEL,
            "max_tokens": 350,
            "system": system_prompt,
            "messages": claude_msgs
        }
        resp = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
        if resp.status_code == 200:
            data = resp.json()
            return data["content"][0]["text"].strip()
    except Exception as e:
        print(f"[Claude LLM Error]: {e}")
    return None

def fallback_socratic(user_msg: str, child_name: str = "bolajon") -> str:
    """Tarmoq yoki API vaqtincha ishlamay qolganda beriladigan pedagogik javob."""
    return f"Salom {child_name}! Bu juda ajoyib va qiziq savol bo'ldi. Keling, bu mavzuni birgalikda o'rganamiz va yangi qiziqarli bilimlarni kashf qilamiz!"

async def generate_llm_response(
    messages: List[Dict[str, str]],
    system_prompt: str,
    child_name: str = "bolajon"
) -> Tuple[str, str]:
    """
    Ko'p pog'onali, hech qachon yiqilmaydigan LLM integratsiyasi:
    Groq -> Gemini -> Claude -> Socratic Backup
    Returns: (javob_matni, ishlatilgan_model)
    """
    # 1. Groq Qwen (Eng tezkor)
    reply = await query_groq(messages, system_prompt)
    if reply:
        return reply, "Groq Qwen 27B"

    # 2. Gemini Flash
    reply = await query_gemini(messages, system_prompt)
    if reply:
        return reply, "Google Gemini 2.5 Flash"

    # 3. Claude 3.5 Sonnet
    reply = await query_claude(messages, system_prompt)
    if reply:
        return reply, CLAUDE_MODEL

    # 4. Zaxira pedagogik javob
    return fallback_socratic(messages[-1]["content"] if messages else "", child_name), "Alloma Zaxira Ustoz"
