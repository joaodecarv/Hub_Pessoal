from fastapi import APIRouter, HTTPException
from app.feeds import digest, digest_store

digest_store.init_db()   # make sure the digests table exists on startup

router = APIRouter(prefix="/api/digest", tags=["digest"])

VALID_TOPICS = {"ai", "finance"}


def _check_topic(topic):
    if topic not in VALID_TOPICS:
        raise HTTPException(status_code=400, detail="topic must be 'ai' or 'finance'")


@router.get("")
def get_digest(topic: str):
    """Return the cached digest for a topic (or null if none cached yet)."""
    _check_topic(topic)
    return digest_store.load_digest(topic)


@router.post("/refresh")
def refresh_digest(topic: str):
    """Generate a fresh digest with Gemini, cache it, and return it."""
    _check_topic(topic)
    markdown = digest.build_digest(topic)
    updated_at = digest_store.save_digest(topic, markdown)
    return {"topic": topic, "markdown": markdown, "updated_at": updated_at}
