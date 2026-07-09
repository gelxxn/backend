from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Header, HTTPException
from bson import ObjectId
from config import vocabs_col, progress_col, streaks_col
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

@router.get("/sub/{sub_category:path}")
def get_vocab_progress_by_sub(sub_category: str, authorization: str = Header(...)):
    user_id = get_user_id(authorization)
 
    try:
        user_object_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="รูปแบบ User ID ไม่ถูกต้อง")
 
    docs = progress_col.find(
        {"user_id": user_object_id, "sub_category": sub_category},
        {"vocab_text": 1, "best_score": 1, "_id": 0},
    )
 
    return {d["vocab_text"]: d.get("best_score", 0.0) for d in docs if d.get("vocab_text")}

@router.get("/streak")
def get_streak(authorization: str = Header(...)):
    user_id = get_user_id(authorization)

    try:
        user_object_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="รูปแบบ User ID ไม่ถูกต้อง")

    doc = streaks_col.find_one({"user_id": user_object_id})
    if not doc:
        return {
            "current_streak": 0,
            "practiced_days_this_week": [False] * 7,
            "last_practiced_word": None,
            "last_practiced_level": None,
            "last_practiced_sub_category": None,
            "last_practiced_best_score": 0.0,  # 🔁 เพิ่ม
        }

    return {
        "current_streak": doc.get("current_streak", 0),
        "practiced_days_this_week": doc.get("practiced_days_this_week", [False] * 7),
        "last_practiced_word": doc.get("last_practiced_word"),
        "last_practiced_level": doc.get("last_practiced_level"),
        "last_practiced_sub_category": doc.get("last_practiced_sub_category"),
        "last_practiced_best_score": doc.get("last_practiced_best_score", 0.0),  # 🔁 เพิ่ม
    }


@router.get("/recent")
def get_recent_lessons(limit: int = 3, authorization: str = Header(...)):
    user_id = get_user_id(authorization)
 
    try:
        user_object_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="รูปแบบ User ID ไม่ถูกต้อง")
 
    pipeline = [
        {"$match": {"user_id": user_object_id}},
        {"$sort": {"practiced_at": -1}},
        {"$group": {"_id": "$level", "practiced_at": {"$first": "$practiced_at"}}},
        {"$sort": {"practiced_at": -1}},
        {"$limit": limit},
    ]
    recent = list(progress_col.aggregate(pipeline))
    levels = [r["_id"] for r in recent]
 
    if not levels:
        return []
    
    total_by_level = {
        item["_id"]: item["total"]
        for item in vocabs_col.aggregate([
            {"$match": {"level": {"$in": levels}}},
            {"$group": {"_id": "$level", "total": {"$sum": 1}}},
        ])
    }
    completed_by_level = {
        item["_id"]: item["completed"]
        for item in progress_col.aggregate([
            {"$match": {"user_id": user_object_id, "level": {"$in": levels}, "is_completed": True}},
            {"$group": {"_id": "$level", "completed": {"$sum": 1}}},
        ])
    }
 
    result = []
    for lvl in levels:
        total = total_by_level.get(lvl, 0)
        completed = completed_by_level.get(lvl, 0)
        result.append({
            "level": lvl,
            "progress": round(completed / total, 2) if total > 0 else 0.0,
        })
    return result

@router.get("/achievements")
def get_achievements(authorization: str = Header(...)):
    user_id = get_user_id(authorization)
 
    try:
        user_object_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="รูปแบบ User ID ไม่ถูกต้อง")
 
    words_completed = progress_col.count_documents({
        "user_id": user_object_id,
        "is_completed": True,
    })
 
    total_by_level = {
        item["_id"]: item["total"]
        for item in vocabs_col.aggregate([{"$group": {"_id": "$level", "total": {"$sum": 1}}}])
    }
    completed_by_level = {
        item["_id"]: item["completed"]
        for item in progress_col.aggregate([
            {"$match": {"user_id": user_object_id, "is_completed": True}},
            {"$group": {"_id": "$level", "completed": {"$sum": 1}}},
        ])
    }
 
    lessons_completed = sum(
        1
        for lvl, total in total_by_level.items()
        if total > 0 and completed_by_level.get(lvl, 0) >= total
    )
 
    return {
        "lessons_completed": lessons_completed,
        "words_completed": words_completed,
    }
 
def _thai_weekday_index(dt: datetime) -> int:
    return dt.weekday()
 
def _update_streak(user_object_id: ObjectId, vocab_text: str, level: int, sub_category: str, best_score: float):
    now = datetime.now(timezone.utc)
    today = now.date()

    doc = streaks_col.find_one({"user_id": user_object_id})

    if not doc:
        practiced_days = [False] * 7
        practiced_days[_thai_weekday_index(now)] = True
        streaks_col.insert_one({
            "user_id": user_object_id,
            "current_streak": 1,
            "practiced_days_this_week": practiced_days,
            "last_practiced_word": vocab_text,
            "last_practiced_level": level,
            "last_practiced_sub_category": sub_category,
            "last_practiced_best_score": best_score,  # 🔁 เพิ่ม
            "last_updated": now,
        })
        return

    last_updated = doc.get("last_updated")
    last_date = last_updated.date() if last_updated else None

    if last_date == today:
        new_streak = doc.get("current_streak", 1)
        practiced_days = doc.get("practiced_days_this_week", [False] * 7)
    elif last_date == today - timedelta(days=1):
        new_streak = doc.get("current_streak", 0) + 1
        practiced_days = doc.get("practiced_days_this_week", [False] * 7)
    else:
        new_streak = 1
        practiced_days = [False] * 7

    practiced_days[_thai_weekday_index(now)] = True

    streaks_col.update_one(
        {"user_id": user_object_id},
        {"$set": {
            "current_streak": new_streak,
            "practiced_days_this_week": practiced_days,
            "last_practiced_word": vocab_text,
            "last_practiced_level": level,
            "last_practiced_sub_category": sub_category,
            "last_practiced_best_score": best_score,  # 🔁 เพิ่ม
            "last_updated": now,
        }},
    )

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
            "vocab_text": req.vocab_text,  
            "is_completed": req.is_completed,
            "best_score": req.best_score,
            "practiced_at": datetime.now(timezone.utc),
        }},
        upsert=True,
    )

    _update_streak(user_object_id, req.vocab_text, req.level, req.sub_category, req.best_score)  

    return {"status": "ok"}