from __future__ import annotations

import sys

from PySide6.QtCore import Qt, QSize, Signal, QEvent
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class TaskItem(QWidget):
    def __init__(self, text: str):
        super().__init__()
        self.task_text = text

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        self.checkbox = QCheckBox()
        self.checkbox.setCursor(Qt.CursorShape.PointingHandCursor)

        self.label = QLabel(text)
        self.label.setStyleSheet("font-size: 15px; color: #333333;")

        layout.addWidget(self.checkbox)
        layout.addWidget(self.label)
        layout.addStretch()


class EditorActionButton(QPushButton):
    def __init__(self, text: str):
        super().__init__(text)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(28, 28)
        self.setObjectName("editorActionButton")


class TaskEditor(QWidget):
    task_created = Signal(str, str)
    cancelled = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("taskEditor")
        self._setup_ui()
        self._setup_shadow()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        title_row = QHBoxLayout()
        title_row.setSpacing(8)

        self.checkbox = QCheckBox()
        self.checkbox.setEnabled(False)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("New To-Do")
        self.title_input.setObjectName("editorTitleInput")
        self.title_input.returnPressed.connect(self._on_submit)

        title_row.addWidget(self.checkbox)
        title_row.addWidget(self.title_input)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Notes")
        self.notes_input.setObjectName("editorNotesInput")
        self.notes_input.setFixedHeight(60)

        actions_row = QHBoxLayout()
        actions_row.setSpacing(4)
        actions_row.addStretch()

        self.btn_date = EditorActionButton("📅")
        self.btn_tag = EditorActionButton("🏷")
        self.btn_checklist = EditorActionButton("☰")
        self.btn_flag = EditorActionButton("🚩")

        actions_row.addWidget(self.btn_date)
        actions_row.addWidget(self.btn_tag)
        actions_row.addWidget(self.btn_checklist)
        actions_row.addWidget(self.btn_flag)

        layout.addLayout(title_row)
        layout.addWidget(self.notes_input)
        layout.addLayout(actions_row)

    def _setup_shadow(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(Qt.GlobalColor.gray)
        self.setGraphicsEffect(shadow)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self._on_cancel()
        else:
            super().keyPressEvent(event)

    def _on_submit(self):
        title = self.title_input.text().strip()
        if title:
            notes = self.notes_input.toPlainText().strip()
            self.task_created.emit(title, notes)
            self._reset()

    def _on_cancel(self):
        self._reset()
        self.cancelled.emit()

    def _reset(self):
        self.title_input.clear()
        self.notes_input.clear()

    def focus_title(self):
        self.title_input.setFocus()


class TaskListWidget(QListWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("taskList")
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def add_task(self, text: str, position: int = -1):
        item = QListWidgetItem()
        task_widget = TaskItem(text)
        item.setSizeHint(QSize(0, 40))
        if position < 0:
            self.addItem(item)
        else:
            self.insertItem(position, item)
        self.setItemWidget(item, task_widget)


class ToolbarButton(QPushButton):
    def __init__(self, text: str):
        super().__init__(text)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(36, 36)


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
        self.task_editor.task_created.connect(self._on_task_created)
        self.task_editor.cancelled.connect(self._hide_editor)
        content_layout.addWidget(self.task_editor)

        self.task_list = TaskListWidget()

        sample_tasks = [
            "Review open pull requests",
            "Update Nginx virtual server config to pass custom headers",
            "Draft release notes for opentasks v0.1",
            "Check Ansible dependencies",
            "Buy groceries for dinner",
        ]
        for task_text in sample_tasks:
            self.task_list.add_task(task_text)

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
        self.task_editor.setVisible(True)
        self.task_editor.focus_title()

    def _hide_editor(self):
        self.task_editor.setVisible(False)

    def _on_task_created(self, title: str, notes: str):
        self.task_list.add_task(title, position=0)
        self._hide_editor()

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

            #taskEditor {
                background-color: #FFFFFF;
                border-radius: 10px;
                margin-bottom: 16px;
            }

            #editorTitleInput {
                border: none;
                background: transparent;
                font-size: 15px;
                color: #333333;
                padding: 4px;
            }
            #editorTitleInput:focus {
                outline: none;
            }

            #editorNotesInput {
                border: none;
                background: transparent;
                font-size: 13px;
                color: #666666;
                padding: 4px;
            }
            #editorNotesInput:focus {
                outline: none;
            }

            #editorActionButton {
                background: transparent;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                color: #888888;
            }
            #editorActionButton:hover {
                background-color: #F0F0F0;
            }

            #taskList {
                background: transparent;
                border: none;
                outline: none;
            }
            #taskList::item {
                background: transparent;
                border: none;
                border-radius: 6px;
                margin-bottom: 2px;
            }
            #taskList::item:hover {
                background-color: #F0F0F0;
            }
            #taskList::item:selected {
                background-color: #E8E8E8;
            }

            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 1.5px solid #C0C0C0;
                background-color: transparent;
            }
            QCheckBox::indicator:hover {
                border: 1.5px solid #4A90D9;
            }
            QCheckBox::indicator:checked {
                background-color: #4A90D9;
                border: 1.5px solid #4A90D9;
            }
            QCheckBox::indicator:disabled {
                border: 1.5px solid #D0D0D0;
            }

            #bottomToolbar {
                background-color: #2A2A2A;
                border-top: 1px solid #3A3A3A;
            }

            #addButton {
                background-color: #4A90D9;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 20px;
                font-weight: bold;
            }
            #addButton:hover {
                background-color: #5A9FE8;
            }
            #addButton:pressed {
                background-color: #3A80C9;
            }

            #toolbarButton {
                background-color: transparent;
                color: #A0A0A0;
                border: none;
                border-radius: 6px;
                font-size: 16px;
            }
            #toolbarButton:hover {
                background-color: #3A3A3A;
                color: #FFFFFF;
            }
            #toolbarButton:pressed {
                background-color: #4A4A4A;
            }
        """)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
