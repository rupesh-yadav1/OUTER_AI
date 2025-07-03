from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
load_dotenv()

import logging
import sys
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

from backend.auth import router as auth_router, current_user
from backend.db import chat_collection
from backend.router import choose_model
from backend.models import chatgpt, gemini, groq

# ─── Logging Setup ───────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log', encoding='utf-8')
    ]
)
logger = logging.getLogger("backend.main")

# ─── FastAPI Setup ───────────────────────────────────────────────────────
app = FastAPI(
    title="AI Router with JWT Auth",
    description="Production-ready AI model router",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:8000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Models ──────────────────────────────────────────────────────────────
class ChatReq(BaseModel):
    message: str

    class Config:
        str_strip_whitespace = True

class ChatResp(BaseModel):
    provider: str
    model: str
    answer: str
    timestamp: str

# ─── Global Exception Handler ─────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error occurred. Please try again."}
    )

# ─── Health Check ─────────────────────────────────────────────────────────
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

# ─── Auth Router ──────────────────────────────────────────────────────────
app.include_router(auth_router)

# ─── Serve UI Pages ───────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def serve_auth(request: Request):
    f = Path("backend/auth.html")
    if not f.exists():
        return HTMLResponse("<h1>Auth page not found</h1>", status_code=404)
    return HTMLResponse(f.read_text(encoding="utf-8"), media_type="text/html")

@app.get("/chat.html", response_class=HTMLResponse)
async def serve_chat_ui():
    f = Path("backend/chat.html")
    if not f.exists():
        return HTMLResponse("<h1>Chat page not found</h1>", status_code=404)
    return HTMLResponse(f.read_text(encoding="utf-8"), media_type="text/html")

# ─── Main Chat Streaming Endpoint ─────────────────────────────────────────
@app.post("/chat-stream")
async def chat_stream(req: ChatReq, user=Depends(current_user)):
    if not req.message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    if len(req.message) > 4000:
        raise HTTPException(status_code=400, detail="Message too long (max 4000 characters)")

    provider, model_id = choose_model(req.message)
    logger.info(f"[STREAM] User={user['email']} → Provider={provider}, Model={model_id}")

    def token_stream():
        answer = ""
        try:
            if provider == "chatgpt":
                for chunk in chatgpt.chatgpt_stream(req.message, model_id):
                    answer += chunk
                    yield chunk
            elif provider == "groq":
                for chunk in groq.groq_stream(req.message, model_id):
                    answer += chunk
                    yield chunk
            elif provider == "gemini":
                # Streaming or fallback to one-shot
                try:
                    for chunk in gemini.gemini_stream(req.message, model_id):
                        answer += chunk
                        yield chunk
                except Exception as fallback_exc:
                    logger.warning(f"Gemini streaming failed, fallback to normal: {fallback_exc}")
                    final = gemini.gemini_answer(req.message, model_id)
                    answer = final
                    yield final
            else:
                yield "[Error: Unknown provider]"
                return
        except Exception as e:
            logger.error(f"Streaming failure: {e}")
            yield f"[Error]: {str(e)}"
        else:
            # Save chat to history DB after successful generation
            try:
                chat_collection.insert_one({
                    "user_id": user["id"],
                    "email": user["email"],
                    "message": req.message,
                    "answer": answer,
                    "provider": provider,
                    "model": model_id,
                    "timestamp": datetime.utcnow()
                })
            except Exception as db_exc:
                logger.error(f"Failed to save chat history: {db_exc}")

    return StreamingResponse(token_stream(), media_type="text/plain")

# ─── Chat History Endpoint ───────────────────────────────────────────────
@app.get("/history")
async def get_history(user=Depends(current_user)):
    try:
        cursor = (
            chat_collection
            .find({"user_id": user["id"]})
            .sort("timestamp", -1)
            .limit(50)
        )
        history = []
        async for doc in cursor:
            history.append({
                "message":   doc["message"],
                "answer":    doc["answer"],
                "provider":  doc["provider"],
                "model":     doc["model"],
                "timestamp": doc["timestamp"].isoformat(),
            })
        return {"history": history, "count": len(history)}
    except Exception as e:
        logger.error(f"History error: {e}")
        return {"history": [], "count": 0}

# ─── Run App ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        access_log=True
    )
