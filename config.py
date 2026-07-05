import os
import threading #Lock Mechanism
from dotenv import load_dotenv #env
from pymongo import MongoClient #database - Mongo Atlas

load_dotenv()

# ─── Secret ────────────────────────────────────────────
SECRET_KEY = os.environ.get("SECRET_KEY", "maibog-eiei")

# ─── MongoDB ───────────────────────────────────────────
MONGO_URI = os.environ.get("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError("setting MONGO_URI in environment variable")

client = MongoClient(MONGO_URI, 
                     serverSelectionTimeoutMS=5000,
                     tlsAllowInvalidCertificates=True,)

vocab_db = client["Vocabulary"]
vocabs_col = vocab_db["Vocabulary"]

auth_db = client["Auth"]
users_col = auth_db["user"]
progress_col = auth_db["progress"]
streaks_col = auth_db["streaks"]

streaks_col.create_index("user_id", unique=True)
progress_col.create_index([("user_id", 1), ("sub_category", 1)])
progress_col.create_index([("user_id", 1), ("practiced_at", -1)])
progress_col.create_index([("user_id", 1), ("vocab_id", 1)], unique=True)