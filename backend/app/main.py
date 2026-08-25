from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.banco_view.router import router as banco_router
from app.feeds.router import router as digest_router

app=FastAPI(title="Personal Hub API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(digest_router)
app.include_router(banco_router)

@app.get("/api/health")
def health():
    return {"status": "ok"}

