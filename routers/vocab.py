from fastapi import APIRouter, HTTPException
from config import vocabs_col
from utils.auth_utils import parse

router = APIRouter(prefix="/vocabs", tags=["Vocab"])

@router.get("")
def get_all_vocabs():
    docs = list(vocabs_col.find())
    return [parse(d) for d in docs]

@router.get("/levels")
def get_levels():
    pipeline = [
        {"$group": {
            "_id": "$level",
            "main_category": {"$first": "$main_category"},
        }},
        {"$sort": {"_id": 1}},
        {"$project": {
            "level": "$_id",
            "main_category": 1,
            "_id": 0,
        }},
    ]
    return list(vocabs_col.aggregate(pipeline))


@router.get("/level/{level}")
def get_by_level(level: int):
    pipeline = [
        {"$match": {"level": level}},
        {"$group": {
            "_id": "$sub_category",
            "total": {"$sum": 1},
        }},
        {"$sort": {"_id": 1}},
        {"$project": {
            "sub_category": "$_id",
            "total": 1,
            "_id": 0,
        }},
    ]
    result = list(vocabs_col.aggregate(pipeline))
    if not result:
        raise HTTPException(status_code=404, detail="find not founds")
    return result


@router.get("/sub/{sub_category:path}")
def get_by_sub(sub_category: str):
    docs = list(vocabs_col.find(
        {"sub_category": sub_category},
        {
            "_id": 1,
            "vocab_text": 1,
            "level": 1,
            "main_category": 1,
            "sub_category": 1,
            "paired_words": 1,
            "animation": 1,
            "image_url": 1,
        },
        sort=[("order", 1)],
    ))
    if not docs:
        raise HTTPException(status_code=404, detail="find not found")
    return [parse(d) for d in docs]


@router.get("/{vocab_text}")
def get_vocab(vocab_text: str):
    doc = vocabs_col.find_one(
        {"vocab_text": vocab_text},
        {
            "_id": 1,
            "vocab_text": 1,
            "level": 1,
            "main_category": 1,
            "sub_category": 1,
            "paired_words": 1,
            "animation": 1,
            "image_url": 1,
            "lip_landmarks": 1,
            "audio_features": 1,
            "pronunciation_guide": 1,
        },
    )
    if not doc:
        raise HTTPException(status_code=404, detail="can't find this words")
    return parse(doc)