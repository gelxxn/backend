import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

# ─── Secret ────────────────────────────────────────────
SECRET_KEY = os.environ.get("SECRET_KEY", "changeme-later")

# ─── MongoDB ───────────────────────────────────────────
MONGO_URI = os.environ.get("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError("setting MONGO_URI in environment variable")

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)

vocab_db = client["Vocabulary"]
vocabs_col = vocab_db["Vocabulary"]

auth_db = client["Auth"]
users_col = auth_db["user"]
progress_col = auth_db["progress"]

# ─── Whisper small — พอดี RAM Railway free tier ────────
# small model ใช้ RAM ~400MB, int8 ลดการใช้งาน CPU
whisper_model = None
def get_whisper():
    global whisper_model
    if whisper_model is None:
        from faster_whisper import WhisperModel
        whisper_model = WhisperModel("small", device="cpu", compute_type="int8")
    return whisper_model