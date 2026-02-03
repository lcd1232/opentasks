"""Tests for Things3 Cloud sync protocol models."""

from __future__ import annotations

import sys
from pathlib import Path

from opentasks.models import (
    ENTITY_TYPE_TO_MODEL,
    Area,
    ChecklistItem,
    HistoryObject,
    HistoryResponse,
    NoteContent,
    RecurrenceRule,
    Settings,
    StartType,
    Status,
    Tag,
    Task,
    TaskType,
    Tombstone,
)


class TestNoteContent:
    def test_from_raw_none(self) -> None:
        result = NoteContent.from_raw(None)
        assert result is None

    def test_from_raw_complete(self) -> None:
        raw = {"v": "Hello world", "ch": 12345, "t": 1, "_t": "tx"}
        result = NoteContent.from_raw(raw)
        assert result is not None
        assert result.value == "Hello world"
        assert result.checksum == 12345
        assert result.content_type == 1
        assert result.type_tag == "tx"

    def test_from_raw_minimal(self) -> None:
        raw = {}
        result = NoteContent.from_raw(raw)
        assert result is not None
        assert result.value == ""
        assert result.checksum == 0
        assert result.content_type == 1
        assert result.type_tag == "tx"

    def test_to_raw(self) -> None:
        note = NoteContent(
            value="Test note", checksum=999, content_type=1, type_tag="tx"
        )
        raw = note.to_raw()
        assert raw == {"v": "Test note", "ch": 999, "t": 1, "_t": "tx"}


class TestRecurrenceRule:
    def test_from_raw_none(self) -> None:
        result = RecurrenceRule.from_raw(None)
        assert result is None

    def test_from_raw_complete(self) -> None:
        raw = {
            "sr": 1234567890.0,
            "ia": 1234567800.0,
            "rc": 5,
            "ed": 1234567999.0,
            "fu": 2,
            "of": [{"d": 1}],
            "ts": 1,
            "fa": 3,
            "tp": 1,
            "rrv": 4,
        }
        result = RecurrenceRule.from_raw(raw)
        assert result is not None
        assert result.start_date == 1234567890.0
        assert result.initial_after == 1234567800.0
        assert result.recurrence_count == 5
        assert result.end_date == 1234567999.0
        assert result.frequency_unit == 2
        assert result.offsets == [{"d": 1}]
        assert result.task_status == 1
        assert result.frequency_amount == 3
        assert result.recurrence_type == 1
        assert result.rule_version == 4

    def test_from_raw_minimal(self) -> None:
        raw = {}
        result = RecurrenceRule.from_raw(raw)
        assert result is not None
        assert result.start_date is None
        assert result.recurrence_count == 0
        assert result.frequency_amount == 1
        assert result.rule_version == 4


class TestTask:
    def test_from_raw_minimal(self) -> None:
        task = Task.from_raw("uuid-123", {})
        assert task.uuid == "uuid-123"
        assert task.title == ""
        assert task.notes is None
        assert task.start_type == StartType.NOT_STARTED
        assert task.status == Status.OPEN
        assert task.task_type == TaskType.TASK
        assert task.project_ids == []
        assert task.area_ids == []
        assert task.tag_ids == []
        assert task.trashed is False

    def test_from_raw_complete(self) -> None:
        raw = {
            "tt": "My Task",
            "nt": {"v": "Notes here", "ch": 100, "t": 1, "_t": "tx"},
            "st": 1,
            "ss": 3,
            "tp": 1,
            "cd": 1700000000.0,
            "md": 1700000100.0,
            "sp": 1700000200.0,
            "dd": 1700000300.0,
            "sr": 1700000400.0,
            "ix": 5,
            "ti": 3,
            "pr": ["project-1"],
            "ar": ["area-1"],
            "tg": ["tag-1", "tag-2"],
            "tr": True,
            "lt": True,
        }
        task = Task.from_raw("uuid-456", raw)
        assert task.uuid == "uuid-456"
        assert task.title == "My Task"
        assert task.notes is not None
        assert task.notes.value == "Notes here"
        assert task.start_type == StartType.ANYTIME
        assert task.status == Status.COMPLETED
        assert task.task_type == TaskType.PROJECT
        assert task.creation_date == 1700000000.0
        assert task.modification_date == 1700000100.0
        assert task.stop_date == 1700000200.0
        assert task.deadline == 1700000300.0
        assert task.start_date == 1700000400.0
        assert task.index == 5
        assert task.today_index == 3
        assert task.project_ids == ["project-1"]
        assert task.area_ids == ["area-1"]
        assert task.tag_ids == ["tag-1", "tag-2"]
        assert task.trashed is True
        assert task.logically_trashed is True

    def test_is_task_property(self) -> None:
        task = Task.from_raw("uuid", {"tp": 0})
        assert task.is_task is True
        assert task.is_project is False
        assert task.is_heading is False

    def test_is_project_property(self) -> None:
        task = Task.from_raw("uuid", {"tp": 1})
        assert task.is_task is False
        assert task.is_project is True
        assert task.is_heading is False

    def test_is_heading_property(self) -> None:
        task = Task.from_raw("uuid", {"tp": 2})
        assert task.is_task is False
        assert task.is_project is False
        assert task.is_heading is True

    def test_is_completed_property(self) -> None:
        open_task = Task.from_raw("uuid", {"ss": 0})
        completed_task = Task.from_raw("uuid", {"ss": 3})
        cancelled_task = Task.from_raw("uuid", {"ss": 2})
        assert open_task.is_completed is False
        assert completed_task.is_completed is True
        assert cancelled_task.is_completed is False

    def test_is_open_property(self) -> None:
        open_task = Task.from_raw("uuid", {"ss": 0})
        completed_task = Task.from_raw("uuid", {"ss": 3})
        assert open_task.is_open is True
        assert completed_task.is_open is False

    def test_with_recurrence_rule(self) -> None:
        raw = {
            "tt": "Recurring Task",
            "rr": {"sr": 1700000000.0, "fu": 1, "fa": 7},
        }
        task = Task.from_raw("uuid", raw)
        assert task.recurrence_rule is not None
        assert task.recurrence_rule.start_date == 1700000000.0
        assert task.recurrence_rule.frequency_unit == 1
        assert task.recurrence_rule.frequency_amount == 7


class TestChecklistItem:
    def test_from_raw_minimal(self) -> None:
        item = ChecklistItem.from_raw("uuid-123", {})
        assert item.uuid == "uuid-123"
        assert item.title == ""
        assert item.task_ids == []
        assert item.status == Status.OPEN
        assert item.index == 0

    def test_from_raw_complete(self) -> None:
        raw = {
            "tt": "Checklist item",
            "ts": ["task-1", "task-2"],
            "cd": 1700000000.0,
            "md": 1700000100.0,
            "sp": 1700000200.0,
            "ss": 3,
            "ix": 10,
            "lt": True,
        }
        item = ChecklistItem.from_raw("uuid-456", raw)
        assert item.uuid == "uuid-456"
        assert item.title == "Checklist item"
        assert item.task_ids == ["task-1", "task-2"]
        assert item.creation_date == 1700000000.0
        assert item.modification_date == 1700000100.0
        assert item.stop_date == 1700000200.0
        assert item.status == Status.COMPLETED
        assert item.index == 10
        assert item.logically_trashed is True

    def test_is_completed_property(self) -> None:
        open_item = ChecklistItem.from_raw("uuid", {"ss": 0})
        completed_item = ChecklistItem.from_raw("uuid", {"ss": 3})
        assert open_item.is_completed is False
        assert completed_item.is_completed is True


class TestArea:
    def test_from_raw_minimal(self) -> None:
        area = Area.from_raw("uuid-123", {})
        assert area.uuid == "uuid-123"
        assert area.title == ""
        assert area.tag_ids == []
        assert area.index == 0

    def test_from_raw_complete(self) -> None:
        raw = {
            "tt": "Work Area",
            "tg": ["tag-1"],
            "ix": 5,
            "xx": {"custom": "data"},
        }
        area = Area.from_raw("uuid-456", raw)
        assert area.uuid == "uuid-456"
        assert area.title == "Work Area"
        assert area.tag_ids == ["tag-1"]
        assert area.index == 5
        assert area.extra == {"custom": "data"}


class TestTag:
    def test_from_raw_minimal(self) -> None:
        tag = Tag.from_raw("uuid-123", {})
        assert tag.uuid == "uuid-123"
        assert tag.title == ""
        assert tag.parent_names == []
        assert tag.index == 0
        assert tag.shortcut is None

    def test_from_raw_complete(self) -> None:
        raw = {
            "tt": "Important",
            "pn": ["Parent Tag"],
            "ix": 3,
            "sh": "i",
        }
        tag = Tag.from_raw("uuid-456", raw)
        assert tag.uuid == "uuid-456"
        assert tag.title == "Important"
        assert tag.parent_names == ["Parent Tag"]
        assert tag.index == 3
        assert tag.shortcut == "i"


class TestSettings:
    def test_from_raw_minimal(self) -> None:
        settings = Settings.from_raw("uuid-123", {})
        assert settings.uuid == "uuid-123"
        assert settings.group_today is False
        assert settings.login_date is None
        assert settings.login_index == 0
        assert settings.user_settings_account_token is None

    def test_from_raw_complete(self) -> None:
        raw = {
            "grpt": True,
            "ld": 1700000000.0,
            "li": 42,
            "usat": "token-abc",
        }
        settings = Settings.from_raw("uuid-456", raw)
        assert settings.uuid == "uuid-456"
        assert settings.group_today is True
        assert settings.login_date == 1700000000.0
        assert settings.login_index == 42
        assert settings.user_settings_account_token == "token-abc"


class TestTombstone:
    def test_from_raw_minimal(self) -> None:
        tombstone = Tombstone.from_raw("uuid-123", {})
        assert tombstone.uuid == "uuid-123"
        assert tombstone.deleted_object_id == ""
        assert tombstone.deletion_date is None

    def test_from_raw_complete(self) -> None:
        raw = {
            "dloid": "deleted-object-uuid",
            "dld": 1700000000.0,
        }
        tombstone = Tombstone.from_raw("uuid-456", raw)
        assert tombstone.uuid == "uuid-456"
        assert tombstone.deleted_object_id == "deleted-object-uuid"
        assert tombstone.deletion_date == 1700000000.0


class TestHistoryObject:
    def test_from_json(self) -> None:
        raw = {"t": 0, "e": "Task6", "p": {"tt": "My Task"}}
        obj = HistoryObject.from_dict(raw)
        assert obj.update_type == 0
        assert obj.entity_type == "Task6"
        assert obj.properties == {"tt": "My Task"}

    def test_from_json_delta(self) -> None:
        raw = {"t": 1, "e": "Task6", "p": {"tt": "Updated Title"}}
        obj = HistoryObject.from_dict(raw)
        assert obj.update_type == 1
        assert obj.entity_type == "Task6"
        assert obj.properties == {"tt": "Updated Title"}


class TestHistoryResponse:
    def test_from_json(self) -> None:
        raw = {
            "current-item-index": 0,
            "end-total-content-size": 1000,
            "latest-total-content-size": 5000,
            "schema": 312,
            "start-total-content-size": 0,
            "items": [
                {
                    "uuid-1": {"t": 0, "e": "Task6", "p": {"tt": "Task 1"}},
                    "uuid-2": {"t": 0, "e": "Area3", "p": {"tt": "Area 1"}},
                }
            ],
        }
        resp = HistoryResponse.from_dict(raw)
        assert resp.current_item_index == 0
        assert resp.end_total_content_size == 1000
        assert resp.latest_total_content_size == 5000
        assert resp.schema == 312
        assert resp.start_total_content_size == 0
        assert len(resp.items) == 1
        assert "uuid-1" in resp.items[0]
        assert resp.items[0]["uuid-1"].entity_type == "Task6"


class TestEntityTypeMapping:
    def test_all_entity_types_mapped(self) -> None:
        expected = {
            "Task6": Task,
            "ChecklistItem3": ChecklistItem,
            "Area3": Area,
            "Tag4": Tag,
            "Settings5": Settings,
            "Tombstone2": Tombstone,
        }
        assert ENTITY_TYPE_TO_MODEL == expected


class TestEnums:
    def test_start_type_values(self) -> None:
        assert StartType.NOT_STARTED == 0
        assert StartType.ANYTIME == 1
        assert StartType.SOMEDAY == 2

    def test_status_values(self) -> None:
        assert Status.OPEN == 0
        assert Status.CANCELLED == 2
        assert Status.COMPLETED == 3

    def test_task_type_values(self) -> None:
        assert TaskType.TASK == 0
        assert TaskType.PROJECT == 1
        assert TaskType.HEADING == 2
