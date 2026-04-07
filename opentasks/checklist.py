from __future__ import annotations

from PySide6.QtCore import QEvent, QPoint, Qt, Signal
from PySide6.QtGui import QKeyEvent, QMouseEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from .models import ChecklistItemData


class GripHandle(QLabel):
    """Draggable grip handle that emits move signals based on vertical drag."""

    move_requested = Signal(int)

    def __init__(self, parent: QWidget | None = None):
        super().__init__("≡", parent)
        self.setObjectName("checklistGripBtn")
        self.setFixedSize(20, 20)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMouseTracking(True)
        self._drag_start: QPoint | None = None
        self._row_height = 32

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event.globalPosition().toPoint()
            self.grabMouse()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_start is not None:
            delta = event.globalPosition().toPoint().y() - self._drag_start.y()
            if abs(delta) >= self._row_height:
                direction = 1 if delta > 0 else -1
                self.move_requested.emit(direction)
                self._drag_start = event.globalPosition().toPoint()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_start = None
        self.releaseMouse()
        super().mouseReleaseEvent(event)


class ChecklistItemWidget(QFrame):
    delete_requested = Signal()
    move_requested = Signal(int)
    focus_next = Signal()
    focus_previous = Signal()
    enter_pressed = Signal()

    def __init__(self, item: ChecklistItemData, parent: QWidget | None = None):
        super().__init__(parent)
        self.item = item
        self.setObjectName("checklistItemWidget")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(12)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.item.completed)
        self.checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        self.checkbox.stateChanged.connect(self._on_checkbox_changed)
        self.checkbox.setFixedSize(20, 20)

        self.title_input = QLineEdit()
        self.title_input.setText(self.item.title)
        self.title_input.setPlaceholderText("New checklist item")
        self.title_input.setObjectName("checklistItemInput")
        self.title_input.textChanged.connect(self._on_title_changed)
        self.title_input.installEventFilter(self)
        self.title_input.setMinimumHeight(24)

        self.grip_label = GripHandle()
        self.grip_label.move_requested.connect(self.move_requested.emit)
        self.grip_label.setVisible(False)

        layout.addWidget(self.checkbox)
        layout.addWidget(self.title_input, 1)
        layout.addWidget(self.grip_label)

        self.setFixedHeight(32)
        self._update_style()

    def _on_checkbox_changed(self, state: int):
        self.item.completed = state == Qt.CheckState.Checked.value
        self._update_style()

    def _on_title_changed(self, text: str):
        self.item.title = text

    def _update_style(self):
        if self.item.completed:
            self.title_input.setStyleSheet(
                "text-decoration: line-through; color: #999999;"
            )
        elif self.item.cancelled:
            self.title_input.setStyleSheet(
                "text-decoration: line-through; color: #CC6666;"
            )
        else:
            self.title_input.setStyleSheet("color: #333333;")

    def set_cancelled(self, cancelled: bool):
        self.item.cancelled = cancelled
        if cancelled:
            self.item.completed = False
            self.checkbox.setChecked(False)
        self._update_style()

    def eventFilter(self, obj, event: QEvent) -> bool:
        if obj == self.title_input and event.type() == QEvent.Type.FocusIn:
            self._on_focus_in()
        elif obj == self.title_input and event.type() == QEvent.Type.FocusOut:
            self._on_focus_out()
        if obj == self.title_input and event.type() == QEvent.Type.KeyPress:
            if isinstance(event, QKeyEvent):
                key = event.key()
                modifiers = event.modifiers()

                if key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
                    self.enter_pressed.emit()
                    return True
                if key == Qt.Key.Key_Delete or key == Qt.Key.Key_Backspace:
                    if not self.title_input.text():
                        self.delete_requested.emit()
                        return True
                if key == Qt.Key.Key_Up:
                    if modifiers & Qt.KeyboardModifier.ControlModifier:
                        self.move_requested.emit(-1)
                        return True
                    self.focus_previous.emit()
                    return True
                if key == Qt.Key.Key_Down:
                    if modifiers & Qt.KeyboardModifier.ControlModifier:
                        self.move_requested.emit(1)
                        return True
                    self.focus_next.emit()
                    return True
                if (
                    key == Qt.Key.Key_K
                    and modifiers & Qt.KeyboardModifier.ControlModifier
                ):
                    if modifiers & Qt.KeyboardModifier.AltModifier:
                        self.set_cancelled(not self.item.cancelled)
                    else:
                        self.checkbox.setChecked(not self.checkbox.isChecked())
                    return True
        return super().eventFilter(obj, event)

    def enterEvent(self, event):
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self.title_input.hasFocus():
            self.grip_label.setVisible(False)
        super().leaveEvent(event)

    def _on_focus_in(self):
        self.grip_label.setVisible(True)
        self.setStyleSheet(
            "ChecklistItemWidget {"
            "  background-color: rgba(74, 144, 217, 0.08);"
            "  border-radius: 4px;"
            "}"
        )

    def _on_focus_out(self):
        self.grip_label.setVisible(False)
        self.setStyleSheet("")

    def focus_input(self, cursor_pos: int = -1):
        self.title_input.setFocus()
        if cursor_pos < 0:
            self.title_input.setCursorPosition(len(self.title_input.text()))
        else:
            self.title_input.setCursorPosition(
                min(cursor_pos, len(self.title_input.text()))
            )


class ChecklistWidget(QWidget):
    items_changed = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("checklistWidget")
        self._items: list[ChecklistItemWidget] = []
        self._setup_ui()

    def _setup_ui(self):
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(20, 4, 0, 4)
        self._layout.setSpacing(0)

        self._items_container = QWidget()
        self._items_container.setObjectName("checklistItemsContainer")
        self._items_layout = QVBoxLayout(self._items_container)
        self._items_layout.setContentsMargins(0, 0, 0, 0)
        self._items_layout.setSpacing(0)

        self._layout.addWidget(self._items_container)

    def _add_new_item(self, focus: bool = True):
        item_data = ChecklistItemData("")
        self._add_item_widget(item_data, focus=focus)

    def _add_item_widget(
        self, item_data: ChecklistItemData, index: int = -1, focus: bool = True
    ):
        widget = ChecklistItemWidget(item_data)
        widget.delete_requested.connect(lambda w=widget: self._remove_item(w))
        widget.move_requested.connect(lambda d, w=widget: self._move_item(w, d))
        widget.focus_next.connect(lambda w=widget: self._focus_next(w))
        widget.focus_previous.connect(lambda w=widget: self._focus_previous(w))
        widget.enter_pressed.connect(lambda w=widget: self._on_enter(w))

        if index < 0:
            self._items_layout.addWidget(widget)
            self._items.append(widget)
        else:
            self._items_layout.insertWidget(index, widget)
            self._items.insert(index, widget)

        self.items_changed.emit()

        if focus:
            widget.focus_input()

    def _remove_item(self, widget: ChecklistItemWidget):
        idx = self._items.index(widget)
        self._items.remove(widget)
        self._items_layout.removeWidget(widget)
        widget.deleteLater()

        self.items_changed.emit()

        if self._items:
            focus_idx = min(idx, len(self._items) - 1)
            self._items[focus_idx].focus_input()

    def _move_item(self, widget: ChecklistItemWidget, direction: int):
        idx = self._items.index(widget)
        new_idx = idx + direction
        if 0 <= new_idx < len(self._items):
            self._items.remove(widget)
            self._items_layout.removeWidget(widget)
            self._items.insert(new_idx, widget)
            self._items_layout.insertWidget(new_idx, widget)
            widget.focus_input()

    def _on_enter(self, widget: ChecklistItemWidget):
        idx = self._items.index(widget)
        if idx < len(self._items) - 1:
            self._items[idx + 1].focus_input()
        else:
            self._add_new_item()

    def _focus_next(self, widget: ChecklistItemWidget):
        idx = self._items.index(widget)
        pos = widget.title_input.cursorPosition()
        if idx < len(self._items) - 1:
            self._items[idx + 1].focus_input(pos)
        else:
            widget.focus_input()

    def _focus_previous(self, widget: ChecklistItemWidget):
        idx = self._items.index(widget)
        pos = widget.title_input.cursorPosition()
        if idx > 0:
            self._items[idx - 1].focus_input(pos)

    def set_checklist(self, items: list[ChecklistItemData]):
        for widget in self._items[:]:
            self._remove_item(widget)
        for item_data in items:
            self._add_item_widget(item_data, focus=False)

    def get_checklist(self) -> list[ChecklistItemData]:
        return [w.item for w in self._items]

    def focus_first_or_add(self):
        if self._items:
            self._items[0].focus_input()
        else:
            self._add_new_item()

    def has_items(self) -> bool:
        return len(self._items) > 0

    def item_count(self) -> int:
        return len(self._items)

    def required_height(self) -> int:
        if not self._items:
            return 8
        return len(self._items) * 32 + 8
