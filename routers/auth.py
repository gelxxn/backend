import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException
from config import SECRET_KEY, users_col
from models.schemas import RegisterRequest, LoginRequest

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register")
def register(req: RegisterRequest):
    if users_col.find_one({"email": req.email}):
        raise HTTPException(status_code=400, detail="อีเมลนี้ถูกใช้แล้ว")

    hashed = bcrypt.hashpw(req.password.encode('utf-8'), bcrypt.gensalt())
    # convert hash to String before save >> avoid problem about type's driver
    hashed_str = hashed.decode('utf-8')

    user = {
        "email": req.email,
        "password": hashed_str,
        "display_name": req.display_name,
        "created_at": datetime.now(timezone.utc),
    }
    result = users_col.insert_one(user)

    token = jwt.encode(
        {
            "user_id": str(result.inserted_id),
            "exp": datetime.now(timezone.utc) + timedelta(days=30),
        },
        SECRET_KEY,
        algorithm="HS256",
    )
    return {
        "token": token,
        "display_name": req.display_name,
        "user_id": str(result.inserted_id),
        "email": req.email,
    }


@router.post("/login")
def login(req: LoginRequest):
    user = users_col.find_one({"email": req.email})
    if not user:
        raise HTTPException(status_code=401, detail="อีเมลหรือรหัสผ่านไม่ถูกต้อง")
    
    stored_password = user["password"].encode('utf-8') if isinstance(user["password"], str) else user["password"]
    if not bcrypt.checkpw(req.password.encode('utf-8'), stored_password):
        raise HTTPException(status_code=401, detail="อีเมลหรือรหัสผ่านไม่ถูกต้อง")

    token = jwt.encode(
        {
            "user_id": str(user["_id"]),
            "exp": datetime.now(timezone.utc) + timedelta(days=30),
        },
        SECRET_KEY,
        algorithm="HS256",
    )
    return {
        "token": token,
        "display_name": user["display_name"],
        "user_id": str(user["_id"]),
        "email": user["email"],
    }