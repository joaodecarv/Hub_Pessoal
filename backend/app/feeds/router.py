from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.feeds import digest, digest_store, gemini_key

router = APIRouter(prefix="/api/digest", tags=["digest"])

VALID_TOPICS = {"ai", "finance"}


def _check_topic(topic):
    if topic not in VALID_TOPICS:
        raise HTTPException(status_code=400, detail="Tópico inválido: use 'ai' ou 'finance'.")


@router.get("")
def get_digest(topic: str):
    """Return the cached digest for a topic (or null if none cached yet)."""
    _check_topic(topic)
    return digest_store.load_digest(topic)


@router.post("/refresh")
def refresh_digest(topic: str):
    """Generate a fresh digest with Gemini, cache it, and return it."""
    _check_topic(topic)
    try:
        markdown = digest.build_digest(topic)
    except digest.MissingKeyError:
        raise HTTPException(
            status_code=409,
            detail="Chave do Gemini não configurada. Cadastre-a em Configurações → Gemini.",
        )
    updated_at = digest_store.save_digest(topic, markdown)
    return {"topic": topic, "markdown": markdown, "updated_at": updated_at}


config_router = APIRouter(prefix="/api/config", tags=["config"])


class GeminiKeyBody(BaseModel):
    api_key: str


@config_router.get("/gemini")
def gemini_status():
    """Whether a key is configured. The key itself is never returned."""
    return {"configured": gemini_key.get_key() is not None}


@config_router.put("/gemini")
def save_gemini_key(body: GeminiKeyBody):
    key = body.api_key.strip()
    if not key:
        raise HTTPException(status_code=422, detail="Informe a chave do Gemini.")
    gemini_key.save_key(key)
    return {"configured": True}
