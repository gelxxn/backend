from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, vocab, progress, transcribe

app = FastAPI(title="SpeakEase API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Register Routers ──────────────────────────────────
app.include_router(auth.router)
app.include_router(vocab.router)
app.include_router(progress.router)
app.include_router(transcribe.router)


@app.get("/health")
def health():
    from config import client
    client.admin.command("ping")
    return {"status": "ok"}
