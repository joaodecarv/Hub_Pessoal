"""Generate the Hub Pessoal icon: a thin black "$" on a white rounded tile with a hairline border.

Run:  QT_QPA_PLATFORM=offscreen python packaging/make_icon.py
Outputs: packaging/icons/hubpessoal-<size>.png for each size in SIZES.
"""
from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QGuiApplication, QPainter, QPen, QPixmap

SIZES = [64, 128, 256, 512, 1024]
OUT_DIR = Path(__file__).resolve().parent / "icons"
MASTER = 1024  # drawn once at this size, then downscaled, so small sizes stay crisp


def render_master() -> QPixmap:
    pm = QPixmap(MASTER, MASTER)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    # Rounded tile with a small margin, like the desktop icons of other apps.
    margin = MASTER * 0.06
    tile = QRectF(margin, margin, MASTER - 2 * margin, MASTER - 2 * margin)
    radius = tile.width() * 0.225
    border = MASTER * 0.006
    p.setPen(QPen(QColor("#d4d4d4"), border))
    p.setBrush(QColor("white"))
    p.drawRoundedRect(tile.adjusted(border / 2, border / 2, -border / 2, -border / 2), radius, radius)

    font = QFont("Inter")
    font.setWeight(QFont.Weight.Light)
    font.setPixelSize(int(tile.height() * 0.62))
    p.setFont(font)
    p.setPen(QColor("black"))
    p.drawText(tile, Qt.AlignmentFlag.AlignCenter, "$")
    p.end()
    return pm


def main() -> None:
    app = QGuiApplication.instance() or QGuiApplication([])  # noqa: F841 (fonts need a QGuiApplication)
    OUT_DIR.mkdir(exist_ok=True)
    master = render_master()
    for size in SIZES:
        path = OUT_DIR / f"hubpessoal-{size}.png"
        icon = master if size == MASTER else master.scaled(
            size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        icon.save(str(path))
        print("wrote", path)


if __name__ == "__main__":
    main()
