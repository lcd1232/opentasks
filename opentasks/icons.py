from __future__ import annotations

import importlib.resources as pkg_resources
from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtSvg import QSvgRenderer

# Icon name constants (map to SVG filenames without extension)
ICON_TRAY = "tray"
ICON_STAR = "star"
ICON_CALENDAR_BLANK = "calendar-blank"
ICON_CIRCLES_THREE = "circles-three"
ICON_ARCHIVE = "archive"
ICON_BOOK_OPEN = "book-open"
ICON_CALENDAR = "calendar"
ICON_TAG = "tag"
ICON_LIST_CHECKS = "list-checks"
ICON_FLAG = "flag"
ICON_ARROW_RIGHT = "arrow-right"
ICON_MAGNIFYING_GLASS = "magnifying-glass"
ICON_PLUS = "plus"
ICON_CHECK = "check"


def _resources_dir() -> Path:
    return Path(str(pkg_resources.files("opentasks") / "resources"))


@lru_cache(maxsize=64)
def icon_pixmap(name: str, size: int = 16, color: str = "#888888") -> QPixmap:
    """Render a Phosphor SVG icon as a QPixmap at the given size and color."""
    svg_path = _resources_dir() / f"{name}.svg"
    svg_data = svg_path.read_text()
    # Replace the default black stroke/fill with the requested color
    svg_data = svg_data.replace('fill="currentColor"', f'fill="{color}"')
    svg_data = svg_data.replace("#000000", color)
    svg_data = svg_data.replace("#000", color)
    # If no fill was set, add one to the root svg element
    if f'fill="{color}"' not in svg_data:
        svg_data = svg_data.replace("<svg ", f'<svg fill="{color}" ', 1)

    renderer = QSvgRenderer(svg_data.encode())
    pixmap = QPixmap(QSize(size, size))
    pixmap.fill(Qt.GlobalColor.transparent)
    from PySide6.QtGui import QPainter

    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return pixmap


def icon_qicon(name: str, size: int = 16, color: str = "#888888") -> QIcon:
    """Return a QIcon from a Phosphor SVG icon."""
    return QIcon(icon_pixmap(name, size, color))
