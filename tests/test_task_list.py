from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt

from opentasks.models import ChecklistItemData, TaskData
from opentasks.task_list import TaskListWidget


class TestTaskListWidget:
    def test_add_task_increases_count(self, qapp):
        widget = TaskListWidget()
        widget.add_task("Task 1")
        widget.add_task("Task 2")
        assert widget.count() == 2

    def test_add_task_with_metadata(self, qapp):
        widget = TaskListWidget()
        widget.add_task(
            "Task",
            notes="Notes",
            tags=["work"],
            due_date=date.today(),
            project="Project",
            flagged=True,
        )
        assert widget.count() == 1
        task = widget.item(0).data(Qt.ItemDataRole.UserRole)
        assert isinstance(task, TaskData)
        assert task.title == "Task"
        assert task.tags == ["work"]
        assert task.project == "Project"
        assert task.flagged is True

    def test_add_task_at_position(self, qapp):
        widget = TaskListWidget()
        widget.add_task("First")
        widget.add_task("Third")
        widget.add_task("Second", position=1)
        assert widget.count() == 3
        tasks = [
            widget.item(i).data(Qt.ItemDataRole.UserRole).title
            for i in range(widget.count())
        ]
        assert tasks == ["First", "Second", "Third"]

    def test_add_task_with_checklist(self, qapp):
        widget = TaskListWidget()
        checklist = [ChecklistItemData("A"), ChecklistItemData("B")]
        widget.add_task("Task", checklist=checklist)
        task = widget.item(0).data(Qt.ItemDataRole.UserRole)
        assert len(task.checklist) == 2

    def test_delete_selected_task(self, qapp):
        widget = TaskListWidget()
        widget.add_task("Task 1")
        widget.add_task("Task 2")
        widget.setCurrentRow(0)
        widget._delete_selected_task()
        assert widget.count() == 1
        remaining = widget.item(0).data(Qt.ItemDataRole.UserRole)
        assert remaining.title == "Task 2"

    def test_delete_pushes_to_undo_stack(self, qapp):
        widget = TaskListWidget()
        widget.add_task("Task 1")
        widget.setCurrentRow(0)
        widget._delete_selected_task()
        assert len(widget._undo_stack) == 1
        assert widget._undo_stack[0][1].title == "Task 1"

    def test_undo_restores_deleted_task(self, qapp):
        widget = TaskListWidget()
        widget.add_task("Task 1")
        widget.add_task("Task 2")
        widget.setCurrentRow(0)
        widget._delete_selected_task()
        assert widget.count() == 1
        widget.undo()
        assert widget.count() == 2
        restored = widget.item(0).data(Qt.ItemDataRole.UserRole)
        assert restored.title == "Task 1"

    def test_undo_empty_stack_does_nothing(self, qapp):
        widget = TaskListWidget()
        widget.add_task("Task 1")
        widget.undo()
        assert widget.count() == 1

    def test_undo_multiple(self, qapp):
        widget = TaskListWidget()
        widget.add_task("A")
        widget.add_task("B")
        widget.setCurrentRow(0)
        widget._delete_selected_task()
        widget.setCurrentRow(0)
        widget._delete_selected_task()
        assert widget.count() == 0
        widget.undo()
        assert widget.count() == 1
        widget.undo()
        assert widget.count() == 2

    def test_empty_state_visible_when_no_tasks(self, qapp):
        widget = TaskListWidget()
        assert widget._empty_label.isHidden()
        # Empty state is updated via model signals which fire asynchronously
        # but add_task + takeItem trigger rowsInserted/rowsRemoved
        widget.add_task("Task")
        widget.setCurrentRow(0)
        widget._delete_selected_task()
        widget._update_empty_state()
        assert not widget._empty_label.isHidden()

    def test_empty_state_hidden_when_tasks_exist(self, qapp):
        widget = TaskListWidget()
        widget.add_task("Task")
        widget._update_empty_state()
        assert widget._empty_label.isHidden()

    def test_task_checked_pushes_undo(self, qapp):
        widget = TaskListWidget()
        widget.add_task("Task 1")
        item = widget.item(0)
        # Simulate immediate removal (skip timer for test)
        widget._remove_completed(item)
        assert widget.count() == 0
        assert len(widget._undo_stack) == 1
        assert widget._undo_stack[0][1].title == "Task 1"

    def test_insert_task_reconnects_signals(self, qapp):
        widget = TaskListWidget()
        task = TaskData("Restored")
        widget._insert_task(task, 0)
        assert widget.count() == 1
        restored_task = widget.item(0).data(Qt.ItemDataRole.UserRole)
        assert restored_task.title == "Restored"

    def test_cancel_edit_when_not_editing(self, qapp):
        widget = TaskListWidget()
        # Should not raise
        widget._cancel_edit()

    def test_delete_with_no_selection_does_nothing(self, qapp):
        widget = TaskListWidget()
        widget.add_task("Task")
        widget.setCurrentRow(-1)
        widget._delete_selected_task()
        assert widget.count() == 1
