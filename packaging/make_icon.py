"""Generate the Hub Pessoal icon: a black "$" on a white background.

Run:  QT_QPA_PLATFORM=offscreen python packaging/make_icon.py
Outputs: packaging/icons/hubpessoal-<size>.png for each size in SIZES.
"""
from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QGuiApplication, QPainter, QPixmap

SIZES = [64, 128, 256, 512]
OUT_DIR = Path(__file__).resolve().parent / "icons"


def render(size: int) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(QColor("white"))
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    font = QFont("DejaVu Sans")
    font.setBold(True)
    font.setPixelSize(int(size * 0.72))
    p.setFont(font)
    p.setPen(QColor("black"))
    p.drawText(QRectF(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, "$")
    p.end()
    return pm


def main() -> None:
    app = QGuiApplication.instance() or QGuiApplication([])  # noqa: F841 (fonts need a QGuiApplication)
    OUT_DIR.mkdir(exist_ok=True)
    for size in SIZES:
        path = OUT_DIR / f"hubpessoal-{size}.png"
        render(size).save(str(path))
        print("wrote", path)


if __name__ == "__main__":
    main()
