from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QPushButton


class EditorActionButton(QPushButton):
    def __init__(self, icon: QIcon | str, icon_size: int = 16):
        if isinstance(icon, str):
            super().__init__(icon)
        else:
            super().__init__()
            self.setIcon(icon)
            self.setIconSize(QSize(icon_size, icon_size))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(28, 28)
        self.setObjectName("editorActionButton")


class ToolbarButton(QPushButton):
    def __init__(self, icon: QIcon | str, icon_size: int = 20):
        if isinstance(icon, str):
            super().__init__(icon)
        else:
            super().__init__()
            self.setIcon(icon)
            self.setIconSize(QSize(icon_size, icon_size))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(36, 36)
