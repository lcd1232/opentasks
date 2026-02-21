from __future__ import annotations

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .models import ChecklistItemData


class ChecklistItemWidget(QWidget):
    delete_requested = Signal()
    move_requested = Signal(int)
    focus_next = Signal()
    focus_previous = Signal()

    def __init__(self, item: ChecklistItemData, parent: QWidget | None = None):
        super().__init__(parent)
        self.item = item
        self.setObjectName("checklistItemWidget")
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(8)

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

        self.delete_btn = QPushButton("×")
        self.delete_btn.setObjectName("checklistDeleteBtn")
        self.delete_btn.setFixedSize(20, 20)
        self.delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_btn.clicked.connect(self.delete_requested.emit)
        self.delete_btn.setVisible(False)

        layout.addWidget(self.checkbox)
        layout.addWidget(self.title_input, 1)
        layout.addWidget(self.delete_btn)

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
        if obj == self.title_input and event.type() == QEvent.Type.KeyPress:
            if isinstance(event, QKeyEvent):
                key = event.key()
                modifiers = event.modifiers()

                if key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
                    self.focus_next.emit()
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
        self.delete_btn.setVisible(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.delete_btn.setVisible(False)
        super().leaveEvent(event)

    def focus_input(self):
        self.title_input.setFocus()
        self.title_input.setCursorPosition(len(self.title_input.text()))


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

        self._add_btn = QPushButton("+ Add checklist item")
        self._add_btn.setObjectName("checklistAddBtn")
        self._add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._add_btn.clicked.connect(self._add_new_item)
        self._add_btn.setFixedHeight(28)

        self._layout.addWidget(self._items_container)
        self._layout.addWidget(self._add_btn)

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

    def _focus_next(self, widget: ChecklistItemWidget):
        idx = self._items.index(widget)
        if idx < len(self._items) - 1:
            self._items[idx + 1].focus_input()
        else:
            self._add_new_item()

    def _focus_previous(self, widget: ChecklistItemWidget):
        idx = self._items.index(widget)
        if idx > 0:
            self._items[idx - 1].focus_input()

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
            return 28
        return len(self._items) * 32 + 28 + 8
