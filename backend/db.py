# backend/db.py
import os
from motor.motor_asyncio import AsyncIOMotorClient

# ─── Load your Mongo URI from .env ─────────────────────────────────────────────────
MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    raise RuntimeError("MONGODB_URI must be set in .env")

# ─── Create the client & select database ────────────────────────────────────────────
client = AsyncIOMotorClient(MONGODB_URI)
# if your URI ends with /auth_db?…, get_default_database() will return “auth_db”
db = client.get_default_database()

# ─── Your three collections ────────────────────────────────────────────────────────
user_collection  = db["users"]         # ← where you store signup/login users
reset_collection = db["resets"]        # ← where you send/store password‐reset tokens
chat_collection  = db["chat_history"]  # ← where you save every question & answer
