from __future__ import annotations

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .buttons import EditorActionButton
from .checklist import ChecklistWidget
from .models import TaskData


class TaskItem(QWidget):
    def __init__(self, task: TaskData):
        super().__init__()
        self.task = task

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        self.checkbox = QCheckBox()
        self.checkbox.setCursor(Qt.CursorShape.PointingHandCursor)

        self.label = QLabel(task.title)
        self.label.setStyleSheet("font-size: 15px; color: #333333;")

        self.checklist_indicator = QLabel()
        self.checklist_indicator.setObjectName("checklistIndicator")
        self._update_checklist_indicator()

        layout.addWidget(self.checkbox)
        layout.addWidget(self.label)
        layout.addWidget(self.checklist_indicator)
        layout.addStretch()

    def _update_checklist_indicator(self):
        if self.task.checklist:
            completed = sum(1 for item in self.task.checklist if item.completed)
            total = len(self.task.checklist)
            self.checklist_indicator.setText(f"☰ {completed}/{total}")
            self.checklist_indicator.setVisible(True)
        else:
            self.checklist_indicator.setVisible(False)

    def update_from_task(self):
        self.label.setText(self.task.title)
        self._update_checklist_indicator()


class TaskEditor(QWidget):
    submitted = Signal(str, str, list)
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
        self.title_input.installEventFilter(self)

        title_row.addWidget(self.checkbox)
        title_row.addWidget(self.title_input)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Notes")
        self.notes_input.setObjectName("editorNotesInput")
        self.notes_input.setFixedHeight(60)
        self.notes_input.setCursorWidth(2)
        self.notes_input.installEventFilter(self)

        self.checklist_widget = ChecklistWidget()
        self.checklist_widget.setVisible(False)

        actions_row = QHBoxLayout()
        actions_row.setSpacing(4)
        actions_row.addStretch()

        self.btn_date = EditorActionButton("📅")
        self.btn_tag = EditorActionButton("🏷")
        self.btn_checklist = EditorActionButton("☰")
        self.btn_checklist.clicked.connect(self._toggle_checklist)
        self.btn_flag = EditorActionButton("🚩")

        actions_row.addWidget(self.btn_date)
        actions_row.addWidget(self.btn_tag)
        actions_row.addWidget(self.btn_checklist)
        actions_row.addWidget(self.btn_flag)

        layout.addLayout(title_row)
        layout.addWidget(self.notes_input)
        layout.addWidget(self.checklist_widget)
        layout.addLayout(actions_row)

    def _toggle_checklist(self):
        is_visible = not self.checklist_widget.isVisible()
        self.checklist_widget.setVisible(is_visible)
        if is_visible:
            self.checklist_widget.focus_first_or_add()

    def _setup_shadow(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(Qt.GlobalColor.gray)
        self.setGraphicsEffect(shadow)

    def eventFilter(self, obj, event: QEvent) -> bool:
        if event.type() == QEvent.Type.KeyPress:
            if isinstance(event, QKeyEvent):
                key = event.key()
                modifiers = event.modifiers()

                if (
                    key == Qt.Key.Key_C
                    and modifiers & Qt.KeyboardModifier.ControlModifier
                    and modifiers & Qt.KeyboardModifier.ShiftModifier
                ):
                    self._toggle_checklist()
                    return True

                if obj == self.notes_input:
                    if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                        if modifiers & Qt.KeyboardModifier.ShiftModifier:
                            return False
                        self._on_submit()
                        return True
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        modifiers = event.modifiers()

        if key == Qt.Key.Key_Escape:
            self._on_cancel()
        elif (
            key == Qt.Key.Key_C
            and modifiers & Qt.KeyboardModifier.ControlModifier
            and modifiers & Qt.KeyboardModifier.ShiftModifier
        ):
            self._toggle_checklist()
        else:
            super().keyPressEvent(event)

    def _on_submit(self):
        title = self.title_input.text().strip()
        if title:
            notes = self.notes_input.toPlainText().strip()
            checklist = self.checklist_widget.get_checklist()
            self.submitted.emit(title, notes, checklist)

    def _on_cancel(self):
        self.cancelled.emit()

    def set_task(self, task: TaskData):
        self.title_input.setText(task.title)
        self.notes_input.setPlainText(task.notes)
        if task.checklist:
            self.checklist_widget.set_checklist(task.checklist)
            self.checklist_widget.setVisible(True)
        else:
            self.checklist_widget.set_checklist([])
            self.checklist_widget.setVisible(False)

    def clear(self):
        self.title_input.clear()
        self.notes_input.clear()
        self.checklist_widget.set_checklist([])
        self.checklist_widget.setVisible(False)

    def focus_title(self):
        self.title_input.setFocus()
        self.title_input.setCursorPosition(len(self.title_input.text()))


class InlineTaskEditor(QWidget):
    submitted = Signal(str, str, list)
    cancelled = Signal()
    delete_requested = Signal()
    navigate = Signal(int)
    size_changed = Signal(int)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("inlineTaskEditor")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        title_row = QHBoxLayout()
        title_row.setSpacing(8)

        self.checkbox = QCheckBox()
        self.checkbox.setEnabled(False)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Task title")
        self.title_input.setObjectName("inlineEditorTitleInput")
        self.title_input.returnPressed.connect(self._on_submit)
        self.title_input.installEventFilter(self)

        title_row.addWidget(self.checkbox)
        title_row.addWidget(self.title_input)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Notes")
        self.notes_input.setObjectName("inlineEditorNotesInput")
        self.notes_input.setFixedHeight(50)
        self.notes_input.setCursorWidth(2)
        self.notes_input.installEventFilter(self)

        self.checklist_widget = ChecklistWidget()
        self.checklist_widget.setVisible(False)
        self.checklist_widget.items_changed.connect(self._on_checklist_changed)

        actions_row = QHBoxLayout()
        actions_row.setSpacing(4)
        actions_row.addStretch()

        self.btn_date = EditorActionButton("📅")
        self.btn_tag = EditorActionButton("🏷")
        self.btn_checklist = EditorActionButton("☰")
        self.btn_checklist.clicked.connect(self._toggle_checklist)
        self.btn_flag = EditorActionButton("🚩")

        actions_row.addWidget(self.btn_date)
        actions_row.addWidget(self.btn_tag)
        actions_row.addWidget(self.btn_checklist)
        actions_row.addWidget(self.btn_flag)

        layout.addLayout(title_row)
        layout.addWidget(self.notes_input)
        layout.addWidget(self.checklist_widget)
        layout.addLayout(actions_row)

    def _toggle_checklist(self):
        is_visible = not self.checklist_widget.isVisible()
        self.checklist_widget.setVisible(is_visible)
        self._emit_size_changed()
        if is_visible:
            self.checklist_widget.focus_first_or_add()

    def _on_checklist_changed(self):
        if self.checklist_widget.isVisible():
            self._emit_size_changed()

    def _emit_size_changed(self):
        base_height = 140
        if self.checklist_widget.isVisible():
            checklist_height = self.checklist_widget.required_height()
            self.size_changed.emit(base_height + checklist_height)
        else:
            self.size_changed.emit(base_height)

    def eventFilter(self, obj, event: QEvent) -> bool:
        if event.type() == QEvent.Type.KeyPress:
            if isinstance(event, QKeyEvent):
                key = event.key()
                modifiers = event.modifiers()

                if (
                    key == Qt.Key.Key_C
                    and modifiers & Qt.KeyboardModifier.ControlModifier
                    and modifiers & Qt.KeyboardModifier.ShiftModifier
                ):
                    self._toggle_checklist()
                    return True

                if obj == self.notes_input:
                    if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                        if modifiers & Qt.KeyboardModifier.ShiftModifier:
                            return False
                        self._on_submit()
                        return True
                    if key == Qt.Key.Key_Escape:
                        self._on_cancel()
                        return True
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        modifiers = event.modifiers()

        if key == Qt.Key.Key_Escape:
            self._on_cancel()
        elif key == Qt.Key.Key_Delete:
            self.delete_requested.emit()
        elif key == Qt.Key.Key_Up:
            self.navigate.emit(-1)
        elif key == Qt.Key.Key_Down:
            self.navigate.emit(1)
        elif (
            key == Qt.Key.Key_C
            and modifiers & Qt.KeyboardModifier.ControlModifier
            and modifiers & Qt.KeyboardModifier.ShiftModifier
        ):
            self._toggle_checklist()
        else:
            super().keyPressEvent(event)

    def _on_submit(self):
        title = self.title_input.text().strip()
        if title:
            notes = self.notes_input.toPlainText().strip()
            checklist = self.checklist_widget.get_checklist()
            self.submitted.emit(title, notes, checklist)

    def _on_cancel(self):
        self.cancelled.emit()

    def set_task(self, task: TaskData):
        self.title_input.setText(task.title)
        self.notes_input.setPlainText(task.notes)
        if task.checklist:
            self.checklist_widget.set_checklist(task.checklist)
            self.checklist_widget.setVisible(True)
        else:
            self.checklist_widget.set_checklist([])
            self.checklist_widget.setVisible(False)

    def focus_title(self):
        self.title_input.setFocus()
        self.title_input.setCursorPosition(len(self.title_input.text()))
