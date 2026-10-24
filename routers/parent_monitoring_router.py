from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any

from ai_core.child_intelligence import (
    get_child_profile,
    get_child_live_status,
    get_child_full_analytics
)
from ai_core.parent_advisor import (
    generate_parent_report,
    answer_parent_query
)

router = APIRouter()

class AskParentQueryRequest(BaseModel):
    child_id: int
    question: str

@router.get("/analytics/{child_id}", summary="Farzandning to'liq faollik va ta'lim tahlili")
async def get_parent_analytics(child_id: int, days: int = Query(7, ge=1, le=30)):
    profile = get_child_profile(child_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Farzand profili topilmadi")

    analytics = get_child_full_analytics(child_id, days=days)
    return {
        "status": "success",
        "child_id": child_id,
        "analytics": analytics
    }

@router.get("/live-status/{child_id}", summary="Farzandning ayni damda qayerda va nima ish qilayotgani (Real-time)")
async def get_live_status(child_id: int):
    profile = get_child_profile(child_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Farzand profili topilmadi")

    live = get_child_live_status(child_id)
    return {
        "status": "success",
        "child_id": child_id,
        "child_name": profile["name"],
        "live_status": live
    }

@router.get("/ai-report/{child_id}", summary="Ota-ona uchun sun'iy intellekt xulosasi va pedagogik tavsiyalar")
async def get_ai_parent_report(child_id: int):
    profile = get_child_profile(child_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Farzand profili topilmadi")

    report = await generate_parent_report(child_id)
    return report

@router.post("/ask-about-child", summary="Ota-onaning bolasi haqidagi savollariga AI orqali aniq javob olish")
async def ask_about_child_endpoint(req: AskParentQueryRequest):
    q = req.question.strip()
    if not q:
        raise HTTPException(status_code=400, detail="Savol matni bo'sh bo'lishi mumkin emas")

    profile = get_child_profile(req.child_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Farzand profili topilmadi")

    result = await answer_parent_query(req.child_id, q)
    return result
