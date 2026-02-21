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
from .models import ChecklistItemData
from .styles import STYLES
from .task_list import TaskListWidget
from .task_widgets import TaskEditor


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

        main_layout.addWidget(content_row, 1)
        self._setup_bottom_toolbar(main_layout)
        self._apply_styles()

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
            ("📥  Inbox", True),
            ("☀️  Today", False),
            ("📅  Upcoming", False),
            ("〰️  Anytime", False),
            ("📦  Someday", False),
        ]

        for text, is_active in nav_items:
            item = QListWidgetItem(text)
            self.nav_list.addItem(item)
            if is_active:
                self.nav_list.setCurrentItem(item)

        sidebar_layout.addWidget(self.nav_list)
        sidebar_layout.addStretch()

        self.logbook_list = QListWidget()
        self.logbook_list.setObjectName("navList")
        self.logbook_list.setFixedHeight(40)
        self.logbook_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.logbook_list.addItem(QListWidgetItem("📚  Logbook"))
        sidebar_layout.addWidget(self.logbook_list)

        parent_layout.addWidget(self.sidebar)

    def _setup_content_area(self, parent_layout: QHBoxLayout):
        self.content_area = QWidget()
        self.content_area.setObjectName("contentArea")
        content_layout = QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(40, 40, 40, 40)

        self.header = QLabel("Inbox")
        self.header.setObjectName("headerLabel")
        content_layout.addWidget(self.header)

        content_layout.addSpacing(20)

        self.task_editor = TaskEditor()
        self.task_editor.setVisible(False)
        self.task_editor.submitted.connect(self._on_task_created)
        self.task_editor.cancelled.connect(self._hide_editor)
        content_layout.addWidget(self.task_editor)

        self.task_list = TaskListWidget()

        sample_tasks = [
            ("Review open pull requests", "Check for merge conflicts"),
            ("Update Nginx virtual server config to pass custom headers", ""),
            ("Draft release notes for opentasks v0.1", "Include new features"),
            ("Check Ansible dependencies", ""),
            ("Buy groceries for dinner", "Milk, eggs, bread"),
        ]
        for title, notes in sample_tasks:
            self.task_list.add_task(title, notes)

        content_layout.addWidget(self.task_list)

        parent_layout.addWidget(self.content_area)

    def _setup_bottom_toolbar(self, parent_layout: QVBoxLayout):
        self.toolbar = QWidget()
        self.toolbar.setObjectName("bottomToolbar")
        self.toolbar.setFixedHeight(48)

        toolbar_layout = QHBoxLayout(self.toolbar)
        toolbar_layout.setContentsMargins(16, 0, 16, 0)
        toolbar_layout.setSpacing(8)

        self.btn_add = ToolbarButton("+")
        self.btn_add.setObjectName("addButton")
        self.btn_add.clicked.connect(self._show_editor)

        self.btn_calendar = ToolbarButton("📅")
        self.btn_calendar.setObjectName("toolbarButton")

        self.btn_next = ToolbarButton("→")
        self.btn_next.setObjectName("toolbarButton")

        self.btn_search = ToolbarButton("🔍")
        self.btn_search.setObjectName("toolbarButton")

        toolbar_layout.addWidget(self.btn_add)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.btn_calendar)
        toolbar_layout.addWidget(self.btn_next)
        toolbar_layout.addWidget(self.btn_search)

        parent_layout.addWidget(self.toolbar)

    def _show_editor(self):
        self.task_editor.clear()
        self.task_editor.setVisible(True)
        self.task_editor.focus_title()

    def _hide_editor(self):
        self.task_editor.setVisible(False)

    def _on_task_created(
        self, title: str, notes: str, checklist: list[ChecklistItemData]
    ):
        self.task_list.add_task(title, notes, position=0, checklist=checklist)
        self.task_editor.clear()
        self._hide_editor()

    def _apply_styles(self):
        self.setStyleSheet(STYLES)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
