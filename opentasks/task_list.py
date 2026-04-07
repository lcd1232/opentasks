from __future__ import annotations

from datetime import date

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QLabel,
    QListWidget,
    QListWidgetItem,
)

from .models import ChecklistItemData, TaskData
from .task_widgets import InlineTaskEditor, TaskItem


class TaskListWidget(QListWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("taskList")
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._editing_item: QListWidgetItem | None = None
        self._editing_task: TaskData | None = None
        self._is_new_task: bool = False
        self._undo_stack: list[tuple[int, TaskData]] = []

        self._empty_label = QLabel("No to-dos here")
        self._empty_label.setStyleSheet(
            "color: #BBBBBB; font-size: 16px; padding-top: 40px;"
        )
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setParent(self)
        self._empty_label.setVisible(False)

        self.model().rowsInserted.connect(self._update_empty_state)
        self.model().rowsRemoved.connect(self._update_empty_state)

        self.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.itemClicked.connect(self._on_item_clicked)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Delete:
            self._delete_selected_task()
        elif event.key() == Qt.Key.Key_Escape:
            if self._editing_item is not None:
                self._cancel_edit()
            else:
                self.clearSelection()
                self.setCurrentRow(-1)
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            current = self.currentItem()
            if current is not None and self._editing_item is None:
                self._on_item_double_clicked(current)
        elif event.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down):
            if self._editing_item is not None:
                self._cancel_edit()
            super().keyPressEvent(event)
        elif event.key() == Qt.Key.Key_Space:
            self._create_task_below_current()
        elif (
            event.key() == Qt.Key.Key_N
            and event.modifiers() & Qt.KeyboardModifier.ControlModifier
        ):
            self._create_task_below_current()
        elif (
            event.key() == Qt.Key.Key_Z
            and event.modifiers() & Qt.KeyboardModifier.ControlModifier
        ):
            self.undo()
        else:
            super().keyPressEvent(event)

    def _delete_selected_task(self):
        current = self.currentItem()
        if current is None:
            return
        if self._editing_item is not None:
            self._cancel_edit()
        row = self.row(current)
        task = current.data(Qt.ItemDataRole.UserRole)
        if isinstance(task, TaskData):
            self._undo_stack.append((row, task))
        self.takeItem(row)

    def _create_task_below_current(self):
        if self._editing_item is not None:
            self._cancel_edit()

        current = self.currentItem()
        if current is not None:
            position = self.row(current) + 1
        else:
            position = 0

        self.add_task("", "", position)
        new_item = self.item(position)
        self.setCurrentItem(new_item)
        self._is_new_task = True
        self._on_item_double_clicked(new_item)

    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        if item is None:
            self.clearSelection()
            self.setCurrentRow(-1)
            if self._editing_item is not None:
                self._cancel_edit()
        super().mousePressEvent(event)

    def add_task(
        self,
        title: str,
        notes: str = "",
        position: int = -1,
        checklist: list[ChecklistItemData] | None = None,
        tags: list[str] | None = None,
        due_date: date | None = None,
        project: str | None = None,
        flagged: bool = False,
    ):
        task = TaskData(
            title,
            notes,
            checklist=checklist,
            tags=tags,
            due_date=due_date,
            project=project,
            flagged=flagged,
        )
        item = QListWidgetItem()
        task_widget = TaskItem(task)
        task_widget.check_toggled.connect(
            lambda checked, i=item: self._on_task_checked(i, checked)
        )
        item.setSizeHint(QSize(0, task_widget.size_hint_height()))
        item.setData(Qt.ItemDataRole.UserRole, task)
        if position < 0:
            self.addItem(item)
        else:
            self.insertItem(position, item)
        self.setItemWidget(item, task_widget)

    def _update_empty_state(self):
        empty = self.count() == 0
        self._empty_label.setVisible(empty)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._empty_label.setGeometry(self.rect())

    def _on_editor_completed(self, item: QListWidgetItem):
        if self._editing_item is None or self._editing_task is None:
            return
        # Close editor and show task row
        task_widget = TaskItem(self._editing_task)
        task_widget.check_toggled.connect(
            lambda checked, i=item: self._on_task_checked(i, checked)
        )
        item.setSizeHint(QSize(0, task_widget.size_hint_height()))
        self.setItemWidget(item, task_widget)
        self._editing_item = None
        self._editing_task = None
        self._is_new_task = False
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        # Now trigger the check visually
        task_widget.checkbox.setChecked(True)

    def _on_task_checked(self, item: QListWidgetItem, checked: bool):
        if checked:
            QTimer.singleShot(800, lambda: self._remove_completed(item))

    def _remove_completed(self, item: QListWidgetItem):
        row = self.row(item)
        if row >= 0:
            task = item.data(Qt.ItemDataRole.UserRole)
            if isinstance(task, TaskData):
                self._undo_stack.append((row, task))
            self.takeItem(row)

    def undo(self):
        if not self._undo_stack:
            return
        row, task = self._undo_stack.pop()
        row = min(row, self.count())
        self._insert_task(task, row)

    def _insert_task(self, task: TaskData, position: int):
        item = QListWidgetItem()
        task_widget = TaskItem(task)
        task_widget.check_toggled.connect(
            lambda checked, i=item: self._on_task_checked(i, checked)
        )
        item.setSizeHint(QSize(0, task_widget.size_hint_height()))
        item.setData(Qt.ItemDataRole.UserRole, task)
        self.insertItem(position, item)
        self.setItemWidget(item, task_widget)

    def _on_item_clicked(self, item: QListWidgetItem):
        if self._editing_item is not None and item != self._editing_item:
            self._cancel_edit()

    def _on_item_double_clicked(self, item: QListWidgetItem):
        if self._editing_item is not None:
            self._cancel_edit()

        task = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(task, TaskData):
            return

        self._editing_item = item
        self._editing_task = task
        self.setDragDropMode(QAbstractItemView.DragDropMode.NoDragDrop)

        editor = InlineTaskEditor()
        editor.set_task(task)
        editor.submitted.connect(self._on_edit_submitted)
        editor.cancelled.connect(self._cancel_edit)
        editor.delete_requested.connect(self._delete_selected_task)
        editor.navigate.connect(self._on_navigate)
        editor.size_changed.connect(lambda h, i=item: i.setSizeHint(QSize(0, h)))
        editor.completed.connect(lambda i=item: self._on_editor_completed(i))

        base_height = 140
        if task.checklist:
            checklist_height = len(task.checklist) * 32 + 28 + 8
            height = base_height + checklist_height
        else:
            height = base_height
        item.setSizeHint(QSize(0, height))
        self.setItemWidget(item, editor)
        editor.focus_title()

    def _on_edit_submitted(
        self, title: str, notes: str, checklist: list[ChecklistItemData]
    ):
        if self._editing_item is None or self._editing_task is None:
            return

        if not title and self._is_new_task:
            row = self.row(self._editing_item)
            self.takeItem(row)
        else:
            self._editing_task.title = title
            self._editing_task.notes = notes
            self._editing_task.checklist = checklist

            task_widget = TaskItem(self._editing_task)
            self._editing_item.setSizeHint(QSize(0, task_widget.size_hint_height()))
            self.setItemWidget(self._editing_item, task_widget)

        self._editing_item = None
        self._editing_task = None
        self._is_new_task = False
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setFocus()

    def _cancel_edit(self):
        if self._editing_item is None or self._editing_task is None:
            return

        if self._is_new_task and not self._editing_task.title:
            row = self.row(self._editing_item)
            self.takeItem(row)
        else:
            task_widget = TaskItem(self._editing_task)
            self._editing_item.setSizeHint(QSize(0, task_widget.size_hint_height()))
            self.setItemWidget(self._editing_item, task_widget)

        self._editing_item = None
        self._editing_task = None
        self._is_new_task = False
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setFocus()

    def _on_navigate(self, direction: int):
        if self._editing_item is None:
            return

        current_row = self.row(self._editing_item)
        new_row = current_row + direction

        if 0 <= new_row < self.count():
            self._cancel_edit()
            self.setCurrentRow(new_row)
            self.setFocus()
