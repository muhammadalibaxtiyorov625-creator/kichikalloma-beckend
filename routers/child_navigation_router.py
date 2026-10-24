from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from ai_core.child_intelligence import track_child_navigation, get_db

router = APIRouter()

class NavigationTrackRequest(BaseModel):
    user_id: int
    child_id: int
    section_key: str
    section_name: str
    action_type: Optional[str] = "view"
    extra_data: Optional[Dict[str, Any]] = None

@router.post("/track", summary="Bolaning qaysi bo'limga kirganini qayd etish")
async def track_navigation_endpoint(req: NavigationTrackRequest):
    success = track_child_navigation(
        user_id=req.user_id,
        child_id=req.child_id,
        section_key=req.section_key,
        section_name=req.section_name,
        action_type=req.action_type or "view",
        extra_data=req.extra_data
    )
    if not success:
        raise HTTPException(status_code=500, detail="Navigatsiyani qayd etishda xatolik yuz berdi")
    return {"status": "success", "message": "Navigatsiya qayd etildi"}

@router.get("/history/{child_id}", summary="Bolaning bo'limlar bo'yicha harakatlar tarixi (Timeline)")
async def get_navigation_history(child_id: int, limit: int = Query(20, ge=1, le=100)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, section_key, section_name, action_type, extra_data, created_at 
        FROM child_navigation_logs 
        WHERE child_id = ? 
        ORDER BY id DESC LIMIT ?
        """,
        (child_id, limit)
    )
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return {
        "status": "success",
        "child_id": child_id,
        "count": len(rows),
        "history": rows
    }
