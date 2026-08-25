import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

Default_DB= Path.home() / ".local" / "share" / "banco" / "banco.db"
BANCO_DB_PATH=Path(os.getenv("BANCO_DB_PATH", str(Default_DB)))
BANCO_SRC_PATH = Path("/home/joao/Workspaces_VSCODE/Meus_Projetos/Banco")