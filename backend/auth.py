# backend/auth.py
import os, logging
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import JWTError, jwt
from bson import ObjectId

# ← add this import
from backend.db import user_collection, reset_collection  

# ─── Config ─────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE_ME")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MIN", "20"))

pwd_context   = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer()
router        = APIRouter(prefix="/auth", tags=["auth"])


# ─── Pydantic models ────────────────────────────────────────────────────
class SignUpRequest(BaseModel):
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ─── Signup endpoint ────────────────────────────────────────────────────
@router.post("/signup", status_code=201)
async def signup(data: SignUpRequest):
    if await user_collection.find_one({"email": data.email.lower()}):
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = pwd_context.hash(data.password)
    res = await user_collection.insert_one({
        "email": data.email.lower(),
        "hashed_password": hashed
    })
    return {"msg": "User created", "id": str(res.inserted_id)}


# ─── Login → returns JSON `{ access_token, token_type }` ────────────────
@router.post("/token", response_model=Token)
async def login(data: LoginRequest):
    user = await user_collection.find_one({"email": data.email.lower()})
    if not user or not pwd_context.verify(data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    expire  = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": user["email"], "id": str(user["_id"]), "exp": expire}
    token   = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token}


# ─── Dependency to protect other routes with Bearer token ────────────────
async def current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    token = credentials.credentials
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        uid  = data.get("id")
        if not uid:
            raise JWTError()
        user = await user_collection.find_one({"_id": ObjectId(uid)})
        if not user:
            raise JWTError()
        return {"id": str(user["_id"]), "email": user["email"]}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )


# ─── Authenticated Profile Info ─────────────────────────────────────────────
@router.get("/me")
async def get_me(user=Depends(current_user)):
    return {"email": user["email"]}
