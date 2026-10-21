"""Gemini API key storage. The key lives in CONFIG_DIR/.env (mode 600) and is
read on every call, so saving a new key takes effect without a restart. The
process environment (dev: backend/.env loaded by config) is only a fallback."""
import os

from dotenv import dotenv_values

from app import config

VAR = "GEMINI_API_KEY"


def _env_path():
    return config.CONFIG_DIR / ".env"


def get_key():
    saved = dotenv_values(_env_path()).get(VAR) if _env_path().exists() else None
    return (saved or os.getenv(VAR) or "").strip() or None


def save_key(key):
    path = _env_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    kept = []
    if path.exists():
        kept = [l for l in path.read_text().splitlines() if not l.startswith(f"{VAR}=")]
    kept.append(f"{VAR}={key}")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write("\n".join(kept) + "\n")
    os.chmod(path, 0o600)
