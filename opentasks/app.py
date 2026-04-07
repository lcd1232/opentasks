from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

from .buttons import ToolbarButton
from .icons import (
    ICON_ARCHIVE,
    ICON_ARROW_RIGHT,
    ICON_BOOK_OPEN,
    ICON_CALENDAR,
    ICON_CALENDAR_BLANK,
    ICON_CIRCLES_THREE,
    ICON_MAGNIFYING_GLASS,
    ICON_PLUS,
    ICON_STAR,
    ICON_TRAY,
    icon_pixmap,
    icon_qicon,
)
from .models import ChecklistItemData
from .styles import STYLES
from .task_list import TaskListWidget
from .task_widgets import ModalOverlay

SECTION_COLORS = {
    "Inbox": "#4A90D9",
    "Today": "#F2C94C",
    "Upcoming": "#EB5757",
    "Anytime": "#6C6CFF",
    "Someday": "#E8833A",
    "Logbook": "#27AE60",
}

SECTION_ICONS = {
    "Inbox": ICON_TRAY,
    "Today": ICON_STAR,
    "Upcoming": ICON_CALENDAR_BLANK,
    "Anytime": ICON_CIRCLES_THREE,
    "Someday": ICON_ARCHIVE,
    "Logbook": ICON_BOOK_OPEN,
}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("opentasks")
        self.setMinimumSize(800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        content_row = QWidget()
        content_row_layout = QHBoxLayout(content_row)
        content_row_layout.setContentsMargins(0, 0, 0, 0)
        content_row_layout.setSpacing(0)

        self._setup_sidebar(content_row_layout)
        self._setup_content_area(content_row_layout)
        self.nav_list.currentRowChanged.connect(self._on_nav_changed)

        main_layout.addWidget(content_row, 1)
        self._setup_bottom_toolbar(main_layout)
        self._apply_styles()

        self._modal = ModalOverlay(central_widget)
        self._modal.setVisible(False)
        self._modal.editor.submitted.connect(self._on_task_created)
        self._modal.editor.cancelled.connect(self._hide_editor)
        self._modal.closed.connect(self._hide_editor)

    def _setup_sidebar(self, parent_layout: QHBoxLayout):
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(220)
        self.sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(16, 24, 16, 24)

        self.nav_list = QListWidget()
        self.nav_list.setObjectName("navList")
        self.nav_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        nav_items = [
            (ICON_TRAY, "Inbox", True),
            (ICON_STAR, "Today", False),
            (ICON_CALENDAR_BLANK, "Upcoming", False),
            (ICON_CIRCLES_THREE, "Anytime", False),
            (ICON_ARCHIVE, "Someday", False),
        ]

        for icon_name, text, is_active in nav_items:
            item = QListWidgetItem(icon_qicon(icon_name, 16, "#D1D1D1"), text)
            self.nav_list.addItem(item)
            if is_active:
                self.nav_list.setCurrentItem(item)

        sidebar_layout.addWidget(self.nav_list)
        sidebar_layout.addStretch()

        self.logbook_list = QListWidget()
        self.logbook_list.setObjectName("navList")
        self.logbook_list.setFixedHeight(40)
        self.logbook_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.logbook_list.addItem(
            QListWidgetItem(icon_qicon(ICON_BOOK_OPEN, 16, "#D1D1D1"), "Logbook")
        )

        sidebar_layout.addWidget(self.logbook_list)
        parent_layout.addWidget(self.sidebar)

    def _setup_content_area(self, parent_layout: QHBoxLayout):
        self.content_area = QWidget()
        self.content_area.setObjectName("contentArea")
        content_layout = QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(40, 48, 40, 40)

        header_row = QHBoxLayout()
        header_row.setSpacing(12)

        self.header_icon = QLabel()
        self.header_icon.setPixmap(
            icon_pixmap(SECTION_ICONS["Inbox"], 24, SECTION_COLORS["Inbox"])
        )
        self.header_icon.setObjectName("headerIcon")
        self.header_icon.setFixedWidth(30)

        self.header = QLabel("Inbox")
        self.header.setObjectName("headerLabel")

        header_row.addWidget(self.header_icon)
        header_row.addWidget(self.header)
        header_row.addStretch()

        content_layout.addLayout(header_row)
        content_layout.addSpacing(24)

        self.task_list = TaskListWidget()

        from datetime import date

        self.task_list.add_task(
            "Review open pull requests",
            "Check for merge conflicts",
            tags=["work"],
            due_date=date.today(),
            project="Dev Project",
            checklist=[
                ChecklistItemData("Check PR #42", completed=True),
                ChecklistItemData("Check PR #43"),
                ChecklistItemData("Check PR #45"),
            ],
        )
        self.task_list.add_task(
            "Update Nginx virtual server config to pass custom headers",
            "Pass custom headers for auth",
            tags=["ops"],
            project="Infrastructure",
        )
        self.task_list.add_task(
            "Draft release notes for opentasks v0.1",
            "Include new features",
            due_date=date.today(),
        )
        self.task_list.add_task(
            "Check Ansible dependencies",
            "",
            tags=["ops", "urgent"],
        )
        self.task_list.add_task(
            "Buy groceries for dinner",
            "Milk, eggs, bread",
            due_date=date(2026, 4, 8),
            flagged=True,
        )

        content_layout.addWidget(self.task_list)

        parent_layout.addWidget(self.content_area)

    def _setup_bottom_toolbar(self, parent_layout: QVBoxLayout):
        self.toolbar = QWidget()
        self.toolbar.setObjectName("bottomToolbar")
        self.toolbar.setFixedHeight(48)

        toolbar_layout = QHBoxLayout(self.toolbar)
        toolbar_layout.setContentsMargins(16, 0, 16, 0)
        toolbar_layout.setSpacing(8)

        self.btn_add = ToolbarButton(icon_qicon(ICON_PLUS, 20, "#FFFFFF"))
        self.btn_add.setObjectName("addButton")
        self.btn_add.clicked.connect(self._show_editor)

        self.btn_calendar = ToolbarButton(icon_qicon(ICON_CALENDAR, 18, "#A0A0A0"))
        self.btn_calendar.setObjectName("toolbarButton")

        self.btn_next = ToolbarButton(icon_qicon(ICON_ARROW_RIGHT, 18, "#A0A0A0"))
        self.btn_next.setObjectName("toolbarButton")

        self.btn_search = ToolbarButton(
            icon_qicon(ICON_MAGNIFYING_GLASS, 18, "#A0A0A0")
        )
        self.btn_search.setObjectName("toolbarButton")

        toolbar_layout.addWidget(self.btn_add)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.btn_calendar)
        toolbar_layout.addWidget(self.btn_next)
        toolbar_layout.addWidget(self.btn_search)

        parent_layout.addWidget(self.toolbar)

    def _show_editor(self):
        self._modal.editor.clear()
        self._modal.setGeometry(self.centralWidget().rect())
        self._modal.setVisible(True)
        self._modal.raise_()
        self._modal.editor.focus_title()

    def _hide_editor(self):
        self._modal.setVisible(False)

    def _on_task_created(
        self, title: str, notes: str, checklist: list[ChecklistItemData]
    ):
        self.task_list.add_task(title, notes, position=0, checklist=checklist)
        self._modal.editor.clear()
        self._hide_editor()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "_modal"):
            self._modal.setGeometry(self.centralWidget().rect())

    def _on_nav_changed(self, row: int):
        names = ["Inbox", "Today", "Upcoming", "Anytime", "Someday"]
        if 0 <= row < len(names):
            name = names[row]
            self.header.setText(name)
            self.header_icon.setPixmap(
                icon_pixmap(SECTION_ICONS[name], 24, SECTION_COLORS[name])
            )

    def _apply_styles(self):
        self.setStyleSheet(STYLES)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
