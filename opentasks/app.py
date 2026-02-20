from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class TaskItem(QWidget):
    def __init__(self, text: str):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)

        self.checkbox = QCheckBox()
        self.checkbox.setCursor(Qt.CursorShape.PointingHandCursor)

        self.label = QLabel(text)
        self.label.setStyleSheet("font-size: 15px; color: #333333;")

        layout.addWidget(self.checkbox)
        layout.addWidget(self.label)
        layout.addStretch()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("opentasks")
        self.setMinimumSize(800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._setup_sidebar(main_layout)
        self._setup_content_area(main_layout)
        self._apply_styles()

    def _setup_sidebar(self, main_layout: QHBoxLayout):
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

        main_layout.addWidget(self.sidebar)

    def _setup_content_area(self, main_layout: QHBoxLayout):
        self.content_area = QWidget()
        self.content_area.setObjectName("contentArea")
        content_layout = QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(40, 40, 40, 40)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.header = QLabel("Inbox")
        self.header.setObjectName("headerLabel")
        content_layout.addWidget(self.header)

        content_layout.addSpacing(20)

        self.task_scroll = QScrollArea()
        self.task_scroll.setWidgetResizable(True)
        self.task_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.task_scroll.setStyleSheet("background: transparent;")

        self.task_container = QWidget()
        self.task_layout = QVBoxLayout(self.task_container)
        self.task_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.task_layout.setContentsMargins(0, 0, 0, 0)
        self.task_layout.setSpacing(2)

        sample_tasks = [
            "Review open pull requests",
            "Update Nginx virtual server config to pass custom headers",
            "Draft release notes for opentasks v0.1",
            "Check Ansible dependencies",
            "Buy groceries for dinner",
        ]
        for task_text in sample_tasks:
            self.task_layout.addWidget(TaskItem(task_text))

        self.task_scroll.setWidget(self.task_container)
        content_layout.addWidget(self.task_scroll)

        main_layout.addWidget(self.content_area)

    def _apply_styles(self):
        self.setStyleSheet("""
            * {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            }

            #sidebar {
                background-color: #1E1E1E;
            }

            #navList {
                background: transparent;
                border: none;
                outline: none;
            }
            #navList::item {
                color: #D1D1D1;
                padding: 8px 12px;
                margin-bottom: 4px;
                border-radius: 6px;
                font-size: 14px;
            }
            #navList::item:hover {
                background-color: #2A2A2A;
            }
            #navList::item:selected {
                background-color: #4A90D9;
                color: white;
                font-weight: 500;
            }

            #contentArea {
                background-color: #FAFAFA;
            }

            #headerLabel {
                font-size: 28px;
                font-weight: bold;
                color: #222222;
            }

            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 10px;
                border: 2px solid #C0C0C0;
                background-color: transparent;
            }
            QCheckBox::indicator:hover {
                border: 2px solid #4A90D9;
            }
            QCheckBox::indicator:checked {
                background-color: #4A90D9;
                border: 2px solid #4A90D9;
            }
        """)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
