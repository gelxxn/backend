from datetime import datetime, timezone
from fastapi import APIRouter, Header, HTTPException
from bson import ObjectId
from config import vocabs_col, progress_col
from models.schemas import ProgressRequest
from utils.auth_utils import get_user_id

router = APIRouter(prefix="/progress", tags=["Progress"])

@router.get("/all-levels")
def get_all_levels_progress(authorization: str = Header(...)):
    user_id = get_user_id(authorization)

    try:
        user_object_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="รูปแบบ User ID ไม่ถูกต้อง")

    vocab_pipeline = [
        {"$group": {"_id": "$level", "total": {"$sum": 1}}}
    ]
    vocab_counts = list(vocabs_col.aggregate(vocab_pipeline))
    total_by_level = {
        item["_id"]: item["total"]
        for item in vocab_counts
        if item["_id"] is not None
    }

    progress_pipeline = [
        {"$match": {"user_id": user_object_id, "is_completed": True}},
        {"$group": {"_id": "$level", "completed": {"$sum": 1}}},
    ]
    progress_counts = list(progress_col.aggregate(progress_pipeline))
    completed_by_level = {
        item["_id"]: item["completed"]
        for item in progress_counts
        if item["_id"] is not None
    }

    result = {}
    for lvl in range(1, 10):
        total = total_by_level.get(lvl, 0)
        completed = completed_by_level.get(lvl, 0)
        result[str(lvl)] = round(completed / total, 2) if total > 0 else 0.0

    return result

@router.get("/level/{level}")
def get_level_progress(level: int, authorization: str = Header(...)):
    user_id = get_user_id(authorization)

    try:
        user_object_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="รูปแบบ User ID ไม่ถูกต้อง")

    pipeline = [
        {"$match": {"level": level}},
        {"$group": {"_id": "$sub_category", "total": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ]
    sub_categories = list(vocabs_col.aggregate(pipeline))

    completed = list(progress_col.find({
        "user_id": user_object_id,
        "level": level,
        "is_completed": True,
    }))

    completed_by_sub: dict[str, int] = {}
    for p in completed:
        sub = p["sub_category"]
        completed_by_sub[sub] = completed_by_sub.get(sub, 0) + 1

    return [
        {
            "sub_category": s["_id"],
            "total": s["total"],
            "completed": completed_by_sub.get(s["_id"], 0),
            "progress": round(completed_by_sub.get(s["_id"], 0) / s["total"], 2)
            if s["total"] > 0
            else 0.0,
        }
        for s in sub_categories
    ]

@router.post("")
def save_progress(req: ProgressRequest, authorization: str = Header(...)):
    user_id = get_user_id(authorization)
    try:
        user_object_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="รูปแบบ User ID ไม่ถูกต้อง")

    try:
        vocab_object_id = ObjectId(req.vocab_id)
    except Exception:
        vocab_object_id = req.vocab_id 

    progress_col.update_one(
        {"user_id": user_object_id, "vocab_id": vocab_object_id},
        {"$set": {
            "level": req.level,
            "sub_category": req.sub_category,
            "is_completed": req.is_completed,
            "best_score": req.best_score,
            "practiced_at": datetime.now(timezone.utc),
        }},
        upsert=True,
    )
    return {"status": "ok"}