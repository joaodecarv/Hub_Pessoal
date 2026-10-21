import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# XDG base directories. User data never lives next to the code, so a read-only
# install (AppImage) can still write.
_DATA_HOME = Path(os.getenv("XDG_DATA_HOME") or Path.home() / ".local" / "share")
_CONFIG_HOME = Path(os.getenv("XDG_CONFIG_HOME") or Path.home() / ".config")

HUB_DB_PATH = _DATA_HOME / "hubpessoal" / "hub.db"
# Where hub.db lived before it moved to the XDG data dir; copied over once by the bootstrap.
LEGACY_HUB_DB_PATH = Path(__file__).resolve().parent.parent / "hub.db"
BANCO_DB_PATH = Path(os.getenv("BANCO_DB_PATH", str(_DATA_HOME / "banco" / "banco.db")))
CONFIG_DIR = _CONFIG_HOME / "hubpessoal"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
