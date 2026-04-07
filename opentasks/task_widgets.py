from __future__ import annotations

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QColor, QKeyEvent, QPainter
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
from .icons import (
    ICON_CALENDAR,
    ICON_FLAG,
    ICON_LIST_CHECKS,
    ICON_TAG,
    icon_pixmap,
    icon_qicon,
)
from .models import TaskData


class TaskItem(QWidget):
    check_toggled = Signal(bool)

    def __init__(self, task: TaskData):
        super().__init__()
        self.task = task

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 10, 8, 10)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.checkbox = QCheckBox()
        self.checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        self.checkbox.setFixedSize(18, 18)
        self.checkbox.stateChanged.connect(self._on_check_changed)
        layout.addWidget(self.checkbox, 0, Qt.AlignmentFlag.AlignTop)
        layout.addSpacing(16)

        center = QVBoxLayout()
        center.setContentsMargins(0, 0, 0, 0)
        center.setSpacing(2)

        self.title_label = QLabel(task.title)
        self.title_label.setObjectName("taskTitle")
        center.addWidget(self.title_label)

        if task.notes:
            self.notes_label = QLabel(task.notes)
            self.notes_label.setObjectName("taskNotes")
            self.notes_label.setMaximumWidth(400)
            self.notes_label.setWordWrap(False)
            center.addWidget(self.notes_label)

        if task.has_metadata():
            metadata_row = QHBoxLayout()
            metadata_row.setContentsMargins(0, 2, 0, 0)
            metadata_row.setSpacing(8)

            for tag in task.tags:
                tag_label = QLabel(tag)
                tag_label.setObjectName("taskTag")
                metadata_row.addWidget(tag_label)

            date_str = task.due_date_display()
            if date_str:
                date_icon = QLabel()
                date_icon.setPixmap(icon_pixmap(ICON_CALENDAR, 12, "#888888"))
                date_icon.setFixedSize(14, 14)
                date_label = QLabel(date_str)
                date_label.setObjectName("taskDueDate")
                metadata_row.addWidget(date_icon)
                metadata_row.addWidget(date_label)

            if task.project:
                project_label = QLabel(task.project)
                project_label.setObjectName("taskProject")
                metadata_row.addWidget(project_label)

            if task.flagged:
                flag_label = QLabel()
                flag_label.setPixmap(icon_pixmap(ICON_FLAG, 12, "#E8833A"))
                flag_label.setFixedSize(14, 14)
                metadata_row.addWidget(flag_label)

            metadata_row.addStretch()
            center.addLayout(metadata_row)

        layout.addLayout(center, 1)

        if task.checklist:
            completed = sum(1 for item in task.checklist if item.completed)
            total = len(task.checklist)
            self.checklist_indicator = QLabel(f"☰ {completed}/{total}")
            self.checklist_indicator.setObjectName("checklistIndicator")
            layout.addWidget(self.checklist_indicator)

    def _on_check_changed(self, state: int):
        checked = state == Qt.CheckState.Checked.value
        self.check_toggled.emit(checked)
        if checked:
            self.setStyleSheet("QWidget { opacity: 0.4; }")
            self.title_label.setStyleSheet(
                "font-size: 15px; color: #999999; text-decoration: line-through;"
            )
        else:
            self.setStyleSheet("")
            self.title_label.setStyleSheet("")

    def update_from_task(self):
        self.title_label.setText(self.task.title)

    def size_hint_height(self) -> int:
        """Return the preferred height based on content."""
        height = 42
        if self.task.notes:
            height += 16
        if self.task.has_metadata():
            height += 18
        return height


class TaskEditor(QWidget):
    submitted = Signal(str, str, list)
    cancelled = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("taskEditor")
        self._setup_ui()

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

        self.btn_date = EditorActionButton(icon_qicon(ICON_CALENDAR, 16, "#888888"))
        self.btn_tag = EditorActionButton(icon_qicon(ICON_TAG, 16, "#888888"))
        self.btn_checklist = EditorActionButton(
            icon_qicon(ICON_LIST_CHECKS, 16, "#888888")
        )
        self.btn_checklist.clicked.connect(self._toggle_checklist)
        self.btn_flag = EditorActionButton(icon_qicon(ICON_FLAG, 16, "#888888"))

        actions_row.addWidget(self.btn_date)
        actions_row.addWidget(self.btn_tag)
        actions_row.addWidget(self.btn_checklist)
        actions_row.addWidget(self.btn_flag)

        layout.addLayout(title_row)
        layout.addWidget(self.notes_input)
        layout.addWidget(self.checklist_widget)
        layout.addLayout(actions_row)

    def _toggle_checklist(self):
        is_visible = self.checklist_widget.isHidden()
        self.checklist_widget.setVisible(is_visible)
        if is_visible:
            self.checklist_widget.focus_first_or_add()

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
            self.btn_checklist.setVisible(False)
        else:
            self.checklist_widget.set_checklist([])
            self.checklist_widget.setVisible(False)
            self.btn_checklist.setVisible(True)

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
    completed = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("inlineTaskEditor")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 10, 8, 8)
        layout.setSpacing(4)

        title_row = QHBoxLayout()
        title_row.setSpacing(16)

        self.checkbox = QCheckBox()
        self.checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        self.checkbox.setFixedSize(18, 18)
        self.checkbox.stateChanged.connect(self._on_check_changed)

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
        self.notes_input.setMinimumHeight(30)
        self.notes_input.setMaximumHeight(200)
        self.notes_input.setCursorWidth(2)
        self.notes_input.installEventFilter(self)
        self.notes_input.document().contentsChanged.connect(self._adjust_notes_height)

        self.checklist_widget = ChecklistWidget()
        self.checklist_widget.setVisible(False)
        self.checklist_widget.items_changed.connect(self._on_checklist_changed)

        actions_row = QHBoxLayout()
        actions_row.setSpacing(4)
        actions_row.addStretch()

        self.btn_date = EditorActionButton(icon_qicon(ICON_CALENDAR, 16, "#888888"))
        self.btn_tag = EditorActionButton(icon_qicon(ICON_TAG, 16, "#888888"))
        self.btn_checklist = EditorActionButton(
            icon_qicon(ICON_LIST_CHECKS, 16, "#888888")
        )
        self.btn_checklist.clicked.connect(self._toggle_checklist)
        self.btn_flag = EditorActionButton(icon_qicon(ICON_FLAG, 16, "#888888"))

        actions_row.addWidget(self.btn_date)
        actions_row.addWidget(self.btn_tag)
        actions_row.addWidget(self.btn_checklist)
        actions_row.addWidget(self.btn_flag)

        layout.addLayout(title_row)
        layout.addWidget(self.notes_input)
        layout.addWidget(self.checklist_widget)
        layout.addLayout(actions_row)

    def _toggle_checklist(self):
        is_visible = self.checklist_widget.isHidden()
        self.checklist_widget.setVisible(is_visible)
        self._emit_size_changed()
        if is_visible:
            self.checklist_widget.focus_first_or_add()

    def _on_checklist_changed(self):
        if not self.checklist_widget.isHidden():
            self._emit_size_changed()

    def _adjust_notes_height(self):
        doc_height = int(self.notes_input.document().size().height()) + 10
        new_height = max(30, min(200, doc_height))
        self.notes_input.setFixedHeight(new_height)
        self._emit_size_changed()

    def _emit_size_changed(self):
        notes_height = self.notes_input.height()
        base_height = 90 + notes_height
        if not self.checklist_widget.isHidden():
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

    def _on_check_changed(self, state: int):
        if state == Qt.CheckState.Checked.value:
            # Save current edits to the task before completing
            title = self.title_input.text().strip()
            if title:
                self._task.title = title
            self._task.notes = self.notes_input.toPlainText().strip()
            self._task.checklist = self.checklist_widget.get_checklist()
            self.completed.emit()

    def _on_submit(self):
        title = self.title_input.text().strip()
        if title:
            notes = self.notes_input.toPlainText().strip()
            checklist = self.checklist_widget.get_checklist()
            self.submitted.emit(title, notes, checklist)

    def _on_cancel(self):
        self.cancelled.emit()

    def set_task(self, task: TaskData):
        self._task = task
        self.title_input.setText(task.title)
        self.notes_input.setPlainText(task.notes)
        if task.checklist:
            self.checklist_widget.set_checklist(task.checklist)
            self.checklist_widget.setVisible(True)
            self.btn_checklist.setVisible(False)
        else:
            self.checklist_widget.set_checklist([])
            self.checklist_widget.setVisible(False)
            self.btn_checklist.setVisible(True)

    def focus_title(self):
        self.title_input.setFocus()
        self.title_input.setCursorPosition(len(self.title_input.text()))


class ModalOverlay(QWidget):
    """Semi-transparent backdrop that hosts the TaskEditor as a centered modal."""

    closed = Signal()

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setObjectName("modalOverlay")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        self._editor = TaskEditor()
        self._editor.setParent(self)
        self._editor.setFixedWidth(500)

        shadow = QGraphicsDropShadowEffect(self._editor)
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(8)
        shadow.setColor(Qt.GlobalColor.gray)
        self._editor.setGraphicsEffect(shadow)

    @property
    def editor(self) -> TaskEditor:
        return self._editor

    def showEvent(self, event):
        super().showEvent(event)
        self._position_editor()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_editor()

    def _position_editor(self):
        editor_height = self._editor.sizeHint().height()
        x = (self.width() - self._editor.width()) // 2
        y = max(80, (self.height() - editor_height) // 3)
        self._editor.move(x, y)

    def mousePressEvent(self, event):
        if not self._editor.geometry().contains(event.position().toPoint()):
            self.closed.emit()
        else:
            super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 77))
        painter.end()
