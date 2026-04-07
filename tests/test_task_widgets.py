from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtTest import QSignalSpy

from opentasks.models import ChecklistItemData, TaskData
from opentasks.task_widgets import (
    InlineTaskEditor,
    ModalOverlay,
    TaskEditor,
    TaskItem,
)


class TestTaskItem:
    def test_title_label_shows_title(self, qapp):
        task = TaskData("Buy milk")
        widget = TaskItem(task)
        assert widget.title_label.text() == "Buy milk"

    def test_notes_label_shown_when_notes_present(self, qapp):
        task = TaskData("Buy milk", notes="Whole milk")
        widget = TaskItem(task)
        assert hasattr(widget, "notes_label")
        assert widget.notes_label.text() == "Whole milk"

    def test_notes_label_not_shown_when_empty(self, qapp):
        task = TaskData("Buy milk")
        widget = TaskItem(task)
        assert not hasattr(widget, "notes_label")

    def test_checklist_indicator_shown(self, qapp):
        task = TaskData(
            "Test",
            checklist=[
                ChecklistItemData("A", completed=True),
                ChecklistItemData("B"),
            ],
        )
        widget = TaskItem(task)
        assert hasattr(widget, "checklist_indicator")
        assert widget.checklist_indicator.text() == "☰ 1/2"

    def test_checklist_indicator_not_shown_without_checklist(self, qapp):
        task = TaskData("Test")
        widget = TaskItem(task)
        assert not hasattr(widget, "checklist_indicator")

    def test_size_hint_height_title_only(self, qapp):
        task = TaskData("Test")
        widget = TaskItem(task)
        assert widget.size_hint_height() == 42

    def test_size_hint_height_with_notes(self, qapp):
        task = TaskData("Test", notes="Some notes")
        widget = TaskItem(task)
        assert widget.size_hint_height() == 42 + 16

    def test_size_hint_height_with_metadata(self, qapp):
        task = TaskData("Test", tags=["work"])
        widget = TaskItem(task)
        assert widget.size_hint_height() == 42 + 18

    def test_size_hint_height_with_notes_and_metadata(self, qapp):
        task = TaskData("Test", notes="Notes", tags=["work"])
        widget = TaskItem(task)
        assert widget.size_hint_height() == 42 + 16 + 18

    def test_check_toggled_signal_emitted(self, qapp):
        task = TaskData("Test")
        widget = TaskItem(task)
        spy = QSignalSpy(widget.check_toggled)
        widget.checkbox.setChecked(True)
        assert spy.count() == 1
        assert spy.at(0)[0] is True

    def test_check_applies_strikethrough_style(self, qapp):
        task = TaskData("Test")
        widget = TaskItem(task)
        widget.checkbox.setChecked(True)
        style = widget.title_label.styleSheet()
        assert "line-through" in style

    def test_uncheck_removes_strikethrough_style(self, qapp):
        task = TaskData("Test")
        widget = TaskItem(task)
        widget.checkbox.setChecked(True)
        widget.checkbox.setChecked(False)
        style = widget.title_label.styleSheet()
        assert "line-through" not in style

    def test_update_from_task(self, qapp):
        task = TaskData("Original")
        widget = TaskItem(task)
        task.title = "Updated"
        widget.update_from_task()
        assert widget.title_label.text() == "Updated"

    def test_metadata_tags_displayed(self, qapp):
        task = TaskData("Test", tags=["work", "urgent"])
        widget = TaskItem(task)
        # Find tag labels by object name
        tag_labels = widget.findChildren(type(widget.title_label), "taskTag")
        assert len(tag_labels) == 2

    def test_metadata_project_displayed(self, qapp):
        task = TaskData("Test", project="Dev Project")
        widget = TaskItem(task)
        project_labels = widget.findChildren(type(widget.title_label), "taskProject")
        assert len(project_labels) == 1
        assert project_labels[0].text() == "Dev Project"

    def test_metadata_due_date_displayed(self, qapp):
        task = TaskData("Test", due_date=date.today())
        widget = TaskItem(task)
        date_labels = widget.findChildren(type(widget.title_label), "taskDueDate")
        assert len(date_labels) == 1
        assert date_labels[0].text() == "Today"


class TestTaskEditor:
    def test_submit_emits_signal(self, qapp):
        editor = TaskEditor()
        spy = QSignalSpy(editor.submitted)
        editor.title_input.setText("New task")
        editor.notes_input.setPlainText("Some notes")
        editor._on_submit()
        assert spy.count() == 1
        assert spy.at(0)[0] == "New task"
        assert spy.at(0)[1] == "Some notes"

    def test_submit_ignores_empty_title(self, qapp):
        editor = TaskEditor()
        spy = QSignalSpy(editor.submitted)
        editor.title_input.setText("")
        editor._on_submit()
        assert spy.count() == 0

    def test_submit_strips_whitespace(self, qapp):
        editor = TaskEditor()
        spy = QSignalSpy(editor.submitted)
        editor.title_input.setText("  Task  ")
        editor._on_submit()
        assert spy.at(0)[0] == "Task"

    def test_cancel_emits_signal(self, qapp):
        editor = TaskEditor()
        spy = QSignalSpy(editor.cancelled)
        editor._on_cancel()
        assert spy.count() == 1

    def test_clear_resets_fields(self, qapp):
        editor = TaskEditor()
        editor.title_input.setText("Task")
        editor.notes_input.setPlainText("Notes")
        editor.clear()
        assert editor.title_input.text() == ""
        assert editor.notes_input.toPlainText() == ""

    def test_set_task_populates_fields(self, qapp):
        editor = TaskEditor()
        task = TaskData("Buy milk", "Whole milk")
        editor.set_task(task)
        assert editor.title_input.text() == "Buy milk"
        assert editor.notes_input.toPlainText() == "Whole milk"

    def test_set_task_with_checklist_shows_checklist(self, qapp):
        editor = TaskEditor()
        task = TaskData("Test", checklist=[ChecklistItemData("Item 1")])
        editor.set_task(task)
        assert not editor.checklist_widget.isHidden()
        assert editor.btn_checklist.isHidden()

    def test_set_task_without_checklist_shows_button(self, qapp):
        editor = TaskEditor()
        task = TaskData("Test")
        editor.set_task(task)
        assert editor.checklist_widget.isHidden()
        assert not editor.btn_checklist.isHidden()

    def test_toggle_checklist(self, qapp):
        editor = TaskEditor()
        assert editor.checklist_widget.isHidden()
        editor._toggle_checklist()
        assert not editor.checklist_widget.isHidden()
        editor._toggle_checklist()
        assert editor.checklist_widget.isHidden()


class TestInlineTaskEditor:
    def test_submit_emits_signal(self, qapp):
        editor = InlineTaskEditor()
        spy = QSignalSpy(editor.submitted)
        editor.title_input.setText("Edited task")
        editor.notes_input.setPlainText("New notes")
        editor._on_submit()
        assert spy.count() == 1
        assert spy.at(0)[0] == "Edited task"

    def test_completed_signal_on_checkbox(self, qapp):
        editor = InlineTaskEditor()
        task = TaskData("Test")
        editor.set_task(task)
        spy = QSignalSpy(editor.completed)
        editor.checkbox.setChecked(True)
        assert spy.count() == 1

    def test_completed_saves_edits_to_task(self, qapp):
        editor = InlineTaskEditor()
        task = TaskData("Original", "Old notes")
        editor.set_task(task)
        editor.title_input.setText("Updated")
        editor.notes_input.setPlainText("New notes")
        editor.checkbox.setChecked(True)
        assert task.title == "Updated"
        assert task.notes == "New notes"

    def test_set_task_with_checklist_hides_button(self, qapp):
        editor = InlineTaskEditor()
        task = TaskData("Test", checklist=[ChecklistItemData("A")])
        editor.set_task(task)
        assert not editor.checklist_widget.isHidden()
        assert editor.btn_checklist.isHidden()

    def test_set_task_without_checklist_shows_button(self, qapp):
        editor = InlineTaskEditor()
        task = TaskData("Test")
        editor.set_task(task)
        assert editor.checklist_widget.isHidden()
        assert not editor.btn_checklist.isHidden()

    def test_checkbox_is_enabled(self, qapp):
        editor = InlineTaskEditor()
        assert editor.checkbox.isEnabled()


class TestModalOverlay:
    def test_editor_accessible(self, qapp):
        from PySide6.QtWidgets import QWidget

        parent = QWidget()
        overlay = ModalOverlay(parent)
        assert isinstance(overlay.editor, TaskEditor)

    def test_editor_has_fixed_width(self, qapp):
        from PySide6.QtWidgets import QWidget

        parent = QWidget()
        overlay = ModalOverlay(parent)
        assert overlay.editor.maximumWidth() == 500 and overlay.editor.minimumWidth() == 500

    def test_closed_signal_on_backdrop_click(self, qapp):
        from PySide6.QtWidgets import QWidget

        parent = QWidget()
        parent.resize(800, 600)
        overlay = ModalOverlay(parent)
        overlay.resize(800, 600)
        spy = QSignalSpy(overlay.closed)
        # Simulate click outside the editor
        from PySide6.QtCore import QPointF
        from PySide6.QtGui import QMouseEvent

        # Click well outside the editor (editor is 500px wide at x=0)
        click_pos = QPointF(overlay.width() - 1, overlay.height() - 1)
        event = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            click_pos,
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        overlay.mousePressEvent(event)
        assert spy.count() == 1
