"""Desktop entrypoint (also the PyInstaller script): `python hub_desktop.py` from backend/."""
import sys

from app.desktop.shell import main

if __name__ == "__main__":
    sys.exit(main())
