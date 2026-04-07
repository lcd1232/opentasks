from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtTest import QSignalSpy

from opentasks.checklist import ChecklistItemWidget, ChecklistWidget
from opentasks.models import ChecklistItemData


class TestChecklistItemWidget:
    def test_displays_title(self, qapp):
        item = ChecklistItemData("Buy eggs")
        widget = ChecklistItemWidget(item)
        assert widget.title_input.text() == "Buy eggs"

    def test_checkbox_reflects_completed(self, qapp):
        item = ChecklistItemData("Done", completed=True)
        widget = ChecklistItemWidget(item)
        assert widget.checkbox.isChecked()

    def test_checkbox_unchecked_by_default(self, qapp):
        item = ChecklistItemData("Todo")
        widget = ChecklistItemWidget(item)
        assert not widget.checkbox.isChecked()

    def test_checking_updates_item_data(self, qapp):
        item = ChecklistItemData("Todo")
        widget = ChecklistItemWidget(item)
        widget.checkbox.setChecked(True)
        assert item.completed is True

    def test_unchecking_updates_item_data(self, qapp):
        item = ChecklistItemData("Done", completed=True)
        widget = ChecklistItemWidget(item)
        widget.checkbox.setChecked(False)
        assert item.completed is False

    def test_text_change_updates_item_data(self, qapp):
        item = ChecklistItemData("Original")
        widget = ChecklistItemWidget(item)
        widget.title_input.setText("Updated")
        assert item.title == "Updated"

    def test_set_cancelled(self, qapp):
        item = ChecklistItemData("Todo")
        widget = ChecklistItemWidget(item)
        widget.set_cancelled(True)
        assert item.cancelled is True
        assert item.completed is False
        assert not widget.checkbox.isChecked()

    def test_grip_hidden_by_default(self, qapp):
        item = ChecklistItemData("Todo")
        widget = ChecklistItemWidget(item)
        assert widget.grip_label.isHidden()

    def test_focus_input_default_cursor_at_end(self, qapp):
        item = ChecklistItemData("Hello")
        widget = ChecklistItemWidget(item)
        widget.focus_input()
        assert widget.title_input.cursorPosition() == 5

    def test_focus_input_with_position(self, qapp):
        item = ChecklistItemData("Hello")
        widget = ChecklistItemWidget(item)
        widget.focus_input(cursor_pos=2)
        assert widget.title_input.cursorPosition() == 2

    def test_focus_input_clamps_position(self, qapp):
        item = ChecklistItemData("Hi")
        widget = ChecklistItemWidget(item)
        widget.focus_input(cursor_pos=100)
        assert widget.title_input.cursorPosition() == 2

    def test_delete_requested_on_backspace_empty(self, qapp):
        item = ChecklistItemData("")
        widget = ChecklistItemWidget(item)
        spy = QSignalSpy(widget.delete_requested)
        from PySide6.QtGui import QKeyEvent
        from PySide6.QtCore import QEvent

        event = QKeyEvent(
            QEvent.Type.KeyPress,
            Qt.Key.Key_Backspace,
            Qt.KeyboardModifier.NoModifier,
        )
        widget.eventFilter(widget.title_input, event)
        assert spy.count() == 1

    def test_enter_emits_enter_pressed(self, qapp):
        item = ChecklistItemData("Test")
        widget = ChecklistItemWidget(item)
        spy = QSignalSpy(widget.enter_pressed)
        from PySide6.QtGui import QKeyEvent
        from PySide6.QtCore import QEvent

        event = QKeyEvent(
            QEvent.Type.KeyPress,
            Qt.Key.Key_Return,
            Qt.KeyboardModifier.NoModifier,
        )
        widget.eventFilter(widget.title_input, event)
        assert spy.count() == 1

    def test_down_arrow_emits_focus_next(self, qapp):
        item = ChecklistItemData("Test")
        widget = ChecklistItemWidget(item)
        spy = QSignalSpy(widget.focus_next)
        from PySide6.QtGui import QKeyEvent
        from PySide6.QtCore import QEvent

        event = QKeyEvent(
            QEvent.Type.KeyPress,
            Qt.Key.Key_Down,
            Qt.KeyboardModifier.NoModifier,
        )
        widget.eventFilter(widget.title_input, event)
        assert spy.count() == 1

    def test_up_arrow_emits_focus_previous(self, qapp):
        item = ChecklistItemData("Test")
        widget = ChecklistItemWidget(item)
        spy = QSignalSpy(widget.focus_previous)
        from PySide6.QtGui import QKeyEvent
        from PySide6.QtCore import QEvent

        event = QKeyEvent(
            QEvent.Type.KeyPress,
            Qt.Key.Key_Up,
            Qt.KeyboardModifier.NoModifier,
        )
        widget.eventFilter(widget.title_input, event)
        assert spy.count() == 1

    def test_ctrl_up_emits_move_requested_minus_1(self, qapp):
        item = ChecklistItemData("Test")
        widget = ChecklistItemWidget(item)
        spy = QSignalSpy(widget.move_requested)
        from PySide6.QtGui import QKeyEvent
        from PySide6.QtCore import QEvent

        event = QKeyEvent(
            QEvent.Type.KeyPress,
            Qt.Key.Key_Up,
            Qt.KeyboardModifier.ControlModifier,
        )
        widget.eventFilter(widget.title_input, event)
        assert spy.count() == 1
        assert spy.at(0)[0] == -1

    def test_ctrl_down_emits_move_requested_plus_1(self, qapp):
        item = ChecklistItemData("Test")
        widget = ChecklistItemWidget(item)
        spy = QSignalSpy(widget.move_requested)
        from PySide6.QtGui import QKeyEvent
        from PySide6.QtCore import QEvent

        event = QKeyEvent(
            QEvent.Type.KeyPress,
            Qt.Key.Key_Down,
            Qt.KeyboardModifier.ControlModifier,
        )
        widget.eventFilter(widget.title_input, event)
        assert spy.count() == 1
        assert spy.at(0)[0] == 1


class TestChecklistWidget:
    def test_empty_by_default(self, qapp):
        widget = ChecklistWidget()
        assert widget.item_count() == 0
        assert not widget.has_items()

    def test_set_checklist(self, qapp):
        widget = ChecklistWidget()
        items = [
            ChecklistItemData("A"),
            ChecklistItemData("B"),
            ChecklistItemData("C"),
        ]
        widget.set_checklist(items)
        assert widget.item_count() == 3

    def test_get_checklist_returns_items(self, qapp):
        widget = ChecklistWidget()
        items = [ChecklistItemData("A"), ChecklistItemData("B")]
        widget.set_checklist(items)
        result = widget.get_checklist()
        assert len(result) == 2
        assert result[0].title == "A"
        assert result[1].title == "B"

    def test_set_checklist_replaces_existing(self, qapp):
        widget = ChecklistWidget()
        widget.set_checklist([ChecklistItemData("Old")])
        widget.set_checklist([ChecklistItemData("New1"), ChecklistItemData("New2")])
        assert widget.item_count() == 2
        result = widget.get_checklist()
        assert result[0].title == "New1"

    def test_move_item_down(self, qapp):
        widget = ChecklistWidget()
        widget.set_checklist(
            [
                ChecklistItemData("A"),
                ChecklistItemData("B"),
                ChecklistItemData("C"),
            ]
        )
        first_widget = widget._items[0]
        widget._move_item(first_widget, 1)
        result = widget.get_checklist()
        assert [r.title for r in result] == ["B", "A", "C"]

    def test_move_item_up(self, qapp):
        widget = ChecklistWidget()
        widget.set_checklist(
            [
                ChecklistItemData("A"),
                ChecklistItemData("B"),
                ChecklistItemData("C"),
            ]
        )
        last_widget = widget._items[2]
        widget._move_item(last_widget, -1)
        result = widget.get_checklist()
        assert [r.title for r in result] == ["A", "C", "B"]

    def test_move_item_past_boundary_does_nothing(self, qapp):
        widget = ChecklistWidget()
        widget.set_checklist([ChecklistItemData("A"), ChecklistItemData("B")])
        first_widget = widget._items[0]
        widget._move_item(first_widget, -1)
        result = widget.get_checklist()
        assert [r.title for r in result] == ["A", "B"]

    def test_remove_item(self, qapp):
        widget = ChecklistWidget()
        widget.set_checklist([ChecklistItemData("A"), ChecklistItemData("B")])
        widget._remove_item(widget._items[0])
        assert widget.item_count() == 1
        assert widget.get_checklist()[0].title == "B"

    def test_enter_on_last_item_adds_new(self, qapp):
        widget = ChecklistWidget()
        widget.set_checklist([ChecklistItemData("A")])
        widget._on_enter(widget._items[0])
        assert widget.item_count() == 2

    def test_enter_on_non_last_item_focuses_next(self, qapp):
        widget = ChecklistWidget()
        widget.set_checklist([ChecklistItemData("A"), ChecklistItemData("B")])
        initial_count = widget.item_count()
        widget._on_enter(widget._items[0])
        assert widget.item_count() == initial_count

    def test_focus_next_on_last_stays_on_last(self, qapp):
        widget = ChecklistWidget()
        widget.set_checklist([ChecklistItemData("A")])
        initial_count = widget.item_count()
        widget._focus_next(widget._items[0])
        assert widget.item_count() == initial_count

    def test_required_height_empty(self, qapp):
        widget = ChecklistWidget()
        assert widget.required_height() == 8

    def test_required_height_with_items(self, qapp):
        widget = ChecklistWidget()
        widget.set_checklist([ChecklistItemData("A"), ChecklistItemData("B")])
        assert widget.required_height() == 2 * 32 + 8

    def test_items_changed_emitted_on_add(self, qapp):
        widget = ChecklistWidget()
        spy = QSignalSpy(widget.items_changed)
        widget.set_checklist([ChecklistItemData("A")])
        assert spy.count() > 0

    def test_has_items(self, qapp):
        widget = ChecklistWidget()
        assert not widget.has_items()
        widget.set_checklist([ChecklistItemData("A")])
        assert widget.has_items()
