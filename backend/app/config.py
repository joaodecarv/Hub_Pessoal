import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


HUB_DB_PATH = Path(__file__).resolve().parent.parent / "hub.db"
Default_DB= Path.home() / ".local" / "share" / "banco" / "banco.db"
BANCO_DB_PATH=Path(os.getenv("BANCO_DB_PATH", str(Default_DB)))
BANCO_SRC_PATH = Path("/home/joao/Workspaces_VSCODE/Meus_Projetos/Banco")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")