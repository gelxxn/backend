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