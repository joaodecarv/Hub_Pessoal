import sys
from pathlib import Path


def get_version():
    """Single source of truth: the VERSION file at the app root (the bundle root when frozen)."""
    root = Path(sys._MEIPASS) if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[2]
    return (root / "VERSION").read_text().strip()
