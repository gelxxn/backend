import jwt
from fastapi import Header, HTTPException
from config import SECRET_KEY


def parse(doc: dict) -> dict:
    doc["_id"] = str(doc["_id"])
    return doc


def get_user_id(authorization: str = Header(...)) -> str:
    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload["user_id"]
    except Exception:
        raise HTTPException(status_code=401, detail="token ไม่ถูกต้อง")