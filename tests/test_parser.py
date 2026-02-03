"""Tests for StateBuilder and State."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from opentasks.models import (
    HistoryObject,
    HistoryResponse,
    Status,
)
from opentasks.parser import StateBuilder


def make_history_response(
    items: list[dict[str, dict]],
    end_total: int = 1000,
    latest_total: int = 1000,
) -> HistoryResponse:
    history_items = []
    for item_group in items:
        group = {}
        for uuid, data in item_group.items():
            group[uuid] = HistoryObject(
                update_type=data["t"],
                entity_type=data["e"],
                properties=data["p"],
            )
        history_items.append(group)
    return HistoryResponse(
        current_item_index=0,
        end_total_content_size=end_total,
        latest_total_content_size=latest_total,
        schema=312,
        start_total_content_size=0,
        items=history_items,
    )


class TestStateBuilderFullSnapshot:
    def test_apply_full_snapshot_task(self) -> None:
        builder = StateBuilder()
        response = make_history_response(
            [
                {
                    "task-1": {"t": 0, "e": "Task6", "p": {"tt": "My Task", "ss": 0}},
                }
            ]
        )
        builder.apply(response)
        state = builder.build()
        assert "task-1" in state.tasks
        assert state.tasks["task-1"].title == "My Task"
        assert state.tasks["task-1"].status == Status.OPEN

    def test_apply_full_snapshot_area(self) -> None:
        builder = StateBuilder()
        response = make_history_response(
            [
                {
                    "area-1": {"t": 0, "e": "Area3", "p": {"tt": "Work", "ix": 5}},
                }
            ]
        )
        builder.apply(response)
        state = builder.build()
        assert "area-1" in state.areas
        assert state.areas["area-1"].title == "Work"
        assert state.areas["area-1"].index == 5

    def test_apply_full_snapshot_tag(self) -> None:
        builder = StateBuilder()
        response = make_history_response(
            [
                {
                    "tag-1": {"t": 0, "e": "Tag4", "p": {"tt": "Important", "sh": "i"}},
                }
            ]
        )
        builder.apply(response)
        state = builder.build()
        assert "tag-1" in state.tags
        assert state.tags["tag-1"].title == "Important"
        assert state.tags["tag-1"].shortcut == "i"

    def test_apply_full_snapshot_checklist_item(self) -> None:
        builder = StateBuilder()
        response = make_history_response(
            [
                {
                    "check-1": {
                        "t": 0,
                        "e": "ChecklistItem3",
                        "p": {"tt": "Step 1", "ts": ["task-1"], "ix": 0},
                    },
                }
            ]
        )
        builder.apply(response)
        state = builder.build()
        assert "check-1" in state.checklist_items
        assert state.checklist_items["check-1"].title == "Step 1"
        assert state.checklist_items["check-1"].task_ids == ["task-1"]

    def test_apply_full_snapshot_settings(self) -> None:
        builder = StateBuilder()
        response = make_history_response(
            [
                {
                    "settings-1": {
                        "t": 0,
                        "e": "Settings5",
                        "p": {"grpt": True, "li": 10},
                    },
                }
            ]
        )
        builder.apply(response)
        state = builder.build()
        assert "settings-1" in state.settings
        assert state.settings["settings-1"].group_today is True
        assert state.settings["settings-1"].login_index == 10

    def test_apply_multiple_objects(self) -> None:
        builder = StateBuilder()
        response = make_history_response(
            [
                {
                    "task-1": {"t": 0, "e": "Task6", "p": {"tt": "Task 1"}},
                    "task-2": {"t": 0, "e": "Task6", "p": {"tt": "Task 2"}},
                    "area-1": {"t": 0, "e": "Area3", "p": {"tt": "Area 1"}},
                }
            ]
        )
        builder.apply(response)
        state = builder.build()
        assert len(state.tasks) == 2
        assert len(state.areas) == 1


class TestStateBuilderDelta:
    def test_apply_delta_updates_existing(self) -> None:
        builder = StateBuilder()
        response1 = make_history_response(
            [
                {
                    "task-1": {
                        "t": 0,
                        "e": "Task6",
                        "p": {"tt": "Original Title", "ss": 0, "ix": 1},
                    },
                }
            ]
        )
        response2 = make_history_response(
            [
                {
                    "task-1": {
                        "t": 1,
                        "e": "Task6",
                        "p": {"tt": "Updated Title"},
                    },
                }
            ]
        )
        builder.apply(response1)
        builder.apply(response2)
        state = builder.build()
        assert state.tasks["task-1"].title == "Updated Title"
        assert state.tasks["task-1"].status == Status.OPEN
        assert state.tasks["task-1"].index == 1

    def test_apply_delta_creates_new_if_missing(self) -> None:
        builder = StateBuilder()
        response = make_history_response(
            [
                {
                    "task-1": {
                        "t": 1,
                        "e": "Task6",
                        "p": {"tt": "New Task via Delta"},
                    },
                }
            ]
        )
        builder.apply(response)
        state = builder.build()
        assert "task-1" in state.tasks
        assert state.tasks["task-1"].title == "New Task via Delta"

    def test_apply_delta_preserves_unmodified_fields(self) -> None:
        builder = StateBuilder()
        response1 = make_history_response(
            [
                {
                    "task-1": {
                        "t": 0,
                        "e": "Task6",
                        "p": {"tt": "Title", "dd": 1700000000.0, "tg": ["tag-1"]},
                    },
                }
            ]
        )
        response2 = make_history_response(
            [
                {
                    "task-1": {
                        "t": 1,
                        "e": "Task6",
                        "p": {"ss": 3},
                    },
                }
            ]
        )
        builder.apply(response1)
        builder.apply(response2)
        state = builder.build()
        assert state.tasks["task-1"].title == "Title"
        assert state.tasks["task-1"].deadline == 1700000000.0
        assert state.tasks["task-1"].tag_ids == ["tag-1"]
        assert state.tasks["task-1"].status == Status.COMPLETED


class TestStateBuilderNotePatch:
    def test_apply_note_patch_insert_at_start(self) -> None:
        builder = StateBuilder()
        response1 = make_history_response(
            [
                {
                    "task-1": {
                        "t": 0,
                        "e": "Task6",
                        "p": {
                            "tt": "Task",
                            "nt": {"_t": "tx", "t": 1, "v": "Hello", "ch": 0},
                        },
                    },
                }
            ]
        )
        response2 = make_history_response(
            [
                {
                    "task-1": {
                        "t": 1,
                        "e": "Task6",
                        "p": {
                            "nt": {
                                "t": 2,
                                "ps": [{"p": 0, "l": 0, "r": "World ", "ch": 100}],
                            }
                        },
                    },
                }
            ]
        )
        builder.apply(response1)
        builder.apply(response2)
        state = builder.build()
        assert state.tasks["task-1"].notes.value == "World Hello"

    def test_apply_note_patch_insert_at_end(self) -> None:
        builder = StateBuilder()
        response1 = make_history_response(
            [
                {
                    "task-1": {
                        "t": 0,
                        "e": "Task6",
                        "p": {
                            "tt": "Task",
                            "nt": {"_t": "tx", "t": 1, "v": "Hello", "ch": 0},
                        },
                    },
                }
            ]
        )
        response2 = make_history_response(
            [
                {
                    "task-1": {
                        "t": 1,
                        "e": "Task6",
                        "p": {
                            "nt": {
                                "t": 2,
                                "ps": [{"p": 5, "l": 0, "r": " World", "ch": 100}],
                            }
                        },
                    },
                }
            ]
        )
        builder.apply(response1)
        builder.apply(response2)
        state = builder.build()
        assert state.tasks["task-1"].notes.value == "Hello World"

    def test_apply_note_patch_delete(self) -> None:
        builder = StateBuilder()
        response1 = make_history_response(
            [
                {
                    "task-1": {
                        "t": 0,
                        "e": "Task6",
                        "p": {
                            "tt": "Task",
                            "nt": {"_t": "tx", "t": 1, "v": "Hello World", "ch": 0},
                        },
                    },
                }
            ]
        )
        response2 = make_history_response(
            [
                {
                    "task-1": {
                        "t": 1,
                        "e": "Task6",
                        "p": {
                            "nt": {
                                "t": 2,
                                "ps": [{"p": 5, "l": 6, "r": "", "ch": 100}],
                            }
                        },
                    },
                }
            ]
        )
        builder.apply(response1)
        builder.apply(response2)
        state = builder.build()
        assert state.tasks["task-1"].notes.value == "Hello"

    def test_apply_note_patch_replace(self) -> None:
        builder = StateBuilder()
        response1 = make_history_response(
            [
                {
                    "task-1": {
                        "t": 0,
                        "e": "Task6",
                        "p": {
                            "tt": "Task",
                            "nt": {"_t": "tx", "t": 1, "v": "Hello World", "ch": 0},
                        },
                    },
                }
            ]
        )
        response2 = make_history_response(
            [
                {
                    "task-1": {
                        "t": 1,
                        "e": "Task6",
                        "p": {
                            "nt": {
                                "t": 2,
                                "ps": [{"p": 6, "l": 5, "r": "Universe", "ch": 100}],
                            }
                        },
                    },
                }
            ]
        )
        builder.apply(response1)
        builder.apply(response2)
        state = builder.build()
        assert state.tasks["task-1"].notes.value == "Hello Universe"

    def test_apply_note_patch_utf8_byte_offsets(self) -> None:
        builder = StateBuilder()
        response1 = make_history_response(
            [
                {
                    "task-1": {
                        "t": 0,
                        "e": "Task6",
                        "p": {
                            "tt": "Task",
                            "nt": {"_t": "tx", "t": 1, "v": "Привет", "ch": 0},
                        },
                    },
                }
            ]
        )
        response2 = make_history_response(
            [
                {
                    "task-1": {
                        "t": 1,
                        "e": "Task6",
                        "p": {
                            "nt": {
                                "t": 2,
                                "ps": [{"p": 12, "l": 0, "r": " мир", "ch": 100}],
                            }
                        },
                    },
                }
            ]
        )
        builder.apply(response1)
        builder.apply(response2)
        state = builder.build()
        assert state.tasks["task-1"].notes.value == "Привет мир"

    def test_apply_note_patch_emoji_byte_offsets(self) -> None:
        builder = StateBuilder()
        response1 = make_history_response(
            [
                {
                    "task-1": {
                        "t": 0,
                        "e": "Task6",
                        "p": {
                            "tt": "Task",
                            "nt": {"_t": "tx", "t": 1, "v": "🎉Test", "ch": 0},
                        },
                    },
                }
            ]
        )
        response2 = make_history_response(
            [
                {
                    "task-1": {
                        "t": 1,
                        "e": "Task6",
                        "p": {
                            "nt": {
                                "t": 2,
                                "ps": [{"p": 4, "l": 0, "r": "🚀", "ch": 100}],
                            }
                        },
                    },
                }
            ]
        )
        builder.apply(response1)
        builder.apply(response2)
        state = builder.build()
        assert state.tasks["task-1"].notes.value == "🎉🚀Test"

    def test_apply_note_patch_multiple_patches(self) -> None:
        builder = StateBuilder()
        response1 = make_history_response(
            [
                {
                    "task-1": {
                        "t": 0,
                        "e": "Task6",
                        "p": {
                            "tt": "Task",
                            "nt": {"_t": "tx", "t": 1, "v": "ABCDEF", "ch": 0},
                        },
                    },
                }
            ]
        )
        response2 = make_history_response(
            [
                {
                    "task-1": {
                        "t": 1,
                        "e": "Task6",
                        "p": {
                            "nt": {
                                "t": 2,
                                "ps": [
                                    {"p": 0, "l": 1, "r": "X", "ch": 50},
                                    {"p": 3, "l": 1, "r": "Y", "ch": 100},
                                ],
                            }
                        },
                    },
                }
            ]
        )
        builder.apply(response1)
        builder.apply(response2)
        state = builder.build()
        assert state.tasks["task-1"].notes.value == "XBCYEF"

    def test_apply_note_patch_to_empty_note(self) -> None:
        builder = StateBuilder()
        response1 = make_history_response(
            [
                {
                    "task-1": {
                        "t": 0,
                        "e": "Task6",
                        "p": {"tt": "Task"},
                    },
                }
            ]
        )
        response2 = make_history_response(
            [
                {
                    "task-1": {
                        "t": 1,
                        "e": "Task6",
                        "p": {
                            "nt": {
                                "t": 2,
                                "ps": [{"p": 0, "l": 0, "r": "New note", "ch": 100}],
                            }
                        },
                    },
                }
            ]
        )
        builder.apply(response1)
        builder.apply(response2)
        state = builder.build()
        assert state.tasks["task-1"].notes.value == "New note"


class TestStateBuilderTombstone:
    def test_tombstone_removes_object(self) -> None:
        builder = StateBuilder()
        response1 = make_history_response(
            [
                {
                    "task-1": {"t": 0, "e": "Task6", "p": {"tt": "To be deleted"}},
                }
            ]
        )
        response2 = make_history_response(
            [
                {
                    "tomb-1": {
                        "t": 0,
                        "e": "Tombstone2",
                        "p": {"dloid": "task-1", "dld": 1700000000.0},
                    },
                }
            ]
        )
        builder.apply(response1)
        builder.apply(response2)
        state = builder.build()
        assert "task-1" not in state.tasks
        assert "task-1" in state.tombstones
        assert state.tombstones["task-1"].deletion_date == 1700000000.0

    def test_tombstone_for_nonexistent_object(self) -> None:
        builder = StateBuilder()
        response = make_history_response(
            [
                {
                    "tomb-1": {
                        "t": 0,
                        "e": "Tombstone2",
                        "p": {"dloid": "never-existed", "dld": 1700000000.0},
                    },
                }
            ]
        )
        builder.apply(response)
        state = builder.build()
        assert "never-existed" in state.tombstones


class TestStateBuilderApplyAll:
    def test_apply_all_multiple_responses(self) -> None:
        builder = StateBuilder()
        responses = [
            make_history_response(
                [{"task-1": {"t": 0, "e": "Task6", "p": {"tt": "Task 1"}}}]
            ),
            make_history_response(
                [{"task-2": {"t": 0, "e": "Task6", "p": {"tt": "Task 2"}}}]
            ),
            make_history_response(
                [{"task-1": {"t": 1, "e": "Task6", "p": {"tt": "Task 1 Updated"}}}]
            ),
        ]
        builder.apply_all(responses)
        state = builder.build()
        assert len(state.tasks) == 2
        assert state.tasks["task-1"].title == "Task 1 Updated"
        assert state.tasks["task-2"].title == "Task 2"


class TestStateProperties:
    def test_projects(self) -> None:
        builder = StateBuilder()
        response = make_history_response(
            [
                {
                    "task-1": {
                        "t": 0,
                        "e": "Task6",
                        "p": {"tt": "Regular Task", "tp": 0},
                    },
                    "proj-1": {
                        "t": 0,
                        "e": "Task6",
                        "p": {"tt": "My Project", "tp": 1},
                    },
                    "head-1": {"t": 0, "e": "Task6", "p": {"tt": "A Heading", "tp": 2}},
                }
            ]
        )
        builder.apply(response)
        state = builder.build()
        assert len(state.projects) == 1
        assert "proj-1" in state.projects
        assert state.projects["proj-1"].title == "My Project"

    def test_headings(self) -> None:
        builder = StateBuilder()
        response = make_history_response(
            [
                {
                    "task-1": {
                        "t": 0,
                        "e": "Task6",
                        "p": {"tt": "Regular Task", "tp": 0},
                    },
                    "head-1": {"t": 0, "e": "Task6", "p": {"tt": "A Heading", "tp": 2}},
                }
            ]
        )
        builder.apply(response)
        state = builder.build()
        assert len(state.headings) == 1
        assert "head-1" in state.headings

    def test_todos_excludes_trashed(self) -> None:
        builder = StateBuilder()
        response = make_history_response(
            [
                {
                    "task-1": {
                        "t": 0,
                        "e": "Task6",
                        "p": {"tt": "Normal", "tp": 0, "tr": False},
                    },
                    "task-2": {
                        "t": 0,
                        "e": "Task6",
                        "p": {"tt": "Trashed", "tp": 0, "tr": True},
                    },
                    "proj-1": {"t": 0, "e": "Task6", "p": {"tt": "Project", "tp": 1}},
                }
            ]
        )
        builder.apply(response)
        state = builder.build()
        assert len(state.todos) == 1
        assert "task-1" in state.todos
        assert "task-2" not in state.todos
        assert "proj-1" not in state.todos

    def test_open_tasks_excludes_trashed(self) -> None:
        builder = StateBuilder()
        response = make_history_response(
            [
                {
                    "task-1": {
                        "t": 0,
                        "e": "Task6",
                        "p": {"tt": "Open", "ss": 0, "tr": False},
                    },
                    "task-2": {
                        "t": 0,
                        "e": "Task6",
                        "p": {"tt": "Completed", "ss": 3, "tr": False},
                    },
                    "task-3": {
                        "t": 0,
                        "e": "Task6",
                        "p": {"tt": "Trashed", "ss": 0, "tr": True},
                    },
                }
            ]
        )
        builder.apply(response)
        state = builder.build()
        assert len(state.open_tasks) == 1
        assert "task-1" in state.open_tasks

    def test_completed_tasks(self) -> None:
        builder = StateBuilder()
        response = make_history_response(
            [
                {
                    "task-1": {"t": 0, "e": "Task6", "p": {"tt": "Open", "ss": 0}},
                    "task-2": {"t": 0, "e": "Task6", "p": {"tt": "Completed", "ss": 3}},
                    "task-3": {"t": 0, "e": "Task6", "p": {"tt": "Cancelled", "ss": 2}},
                }
            ]
        )
        builder.apply(response)
        state = builder.build()
        assert len(state.completed_tasks) == 1
        assert "task-2" in state.completed_tasks


class TestStateMethods:
    def test_tasks_for_project(self) -> None:
        builder = StateBuilder()
        response = make_history_response(
            [
                {
                    "proj-1": {"t": 0, "e": "Task6", "p": {"tt": "Project", "tp": 1}},
                    "task-1": {
                        "t": 0,
                        "e": "Task6",
                        "p": {"tt": "Task A", "pr": ["proj-1"], "ix": 2},
                    },
                    "task-2": {
                        "t": 0,
                        "e": "Task6",
                        "p": {"tt": "Task B", "pr": ["proj-1"], "ix": 1},
                    },
                    "task-3": {
                        "t": 0,
                        "e": "Task6",
                        "p": {"tt": "Other Task", "pr": []},
                    },
                }
            ]
        )
        builder.apply(response)
        state = builder.build()
        project_tasks = state.tasks_for_project("proj-1")
        assert len(project_tasks) == 2
        assert project_tasks[0].title == "Task B"
        assert project_tasks[1].title == "Task A"

    def test_checklist_for_task(self) -> None:
        builder = StateBuilder()
        response = make_history_response(
            [
                {
                    "task-1": {"t": 0, "e": "Task6", "p": {"tt": "Task"}},
                    "check-1": {
                        "t": 0,
                        "e": "ChecklistItem3",
                        "p": {"tt": "Step 1", "ts": ["task-1"], "ix": 2},
                    },
                    "check-2": {
                        "t": 0,
                        "e": "ChecklistItem3",
                        "p": {"tt": "Step 2", "ts": ["task-1"], "ix": 1},
                    },
                    "check-3": {
                        "t": 0,
                        "e": "ChecklistItem3",
                        "p": {"tt": "Other", "ts": ["task-2"], "ix": 0},
                    },
                }
            ]
        )
        builder.apply(response)
        state = builder.build()
        checklist = state.checklist_for_task("task-1")
        assert len(checklist) == 2
        assert checklist[0].title == "Step 2"
        assert checklist[1].title == "Step 1"

    def test_tasks_for_area(self) -> None:
        builder = StateBuilder()
        response = make_history_response(
            [
                {
                    "area-1": {"t": 0, "e": "Area3", "p": {"tt": "Work"}},
                    "task-1": {
                        "t": 0,
                        "e": "Task6",
                        "p": {"tt": "Work Task", "ar": ["area-1"], "ix": 2},
                    },
                    "task-2": {
                        "t": 0,
                        "e": "Task6",
                        "p": {"tt": "Personal Task", "ar": [], "ix": 1},
                    },
                }
            ]
        )
        builder.apply(response)
        state = builder.build()
        area_tasks = state.tasks_for_area("area-1")
        assert len(area_tasks) == 1
        assert area_tasks[0].title == "Work Task"

    def test_tasks_with_tag(self) -> None:
        builder = StateBuilder()
        response = make_history_response(
            [
                {
                    "tag-1": {"t": 0, "e": "Tag4", "p": {"tt": "Important"}},
                    "task-1": {
                        "t": 0,
                        "e": "Task6",
                        "p": {"tt": "Tagged", "tg": ["tag-1"], "ix": 2},
                    },
                    "task-2": {
                        "t": 0,
                        "e": "Task6",
                        "p": {"tt": "Also Tagged", "tg": ["tag-1"], "ix": 1},
                    },
                    "task-3": {"t": 0, "e": "Task6", "p": {"tt": "Untagged", "tg": []}},
                }
            ]
        )
        builder.apply(response)
        state = builder.build()
        tagged_tasks = state.tasks_with_tag("tag-1")
        assert len(tagged_tasks) == 2
        assert tagged_tasks[0].title == "Also Tagged"
        assert tagged_tasks[1].title == "Tagged"


class TestStateBuilderUnknownEntityType:
    def test_unknown_entity_type_ignored(self) -> None:
        builder = StateBuilder()
        response = make_history_response(
            [
                {
                    "task-1": {"t": 0, "e": "Task6", "p": {"tt": "Known"}},
                    "unknown-1": {
                        "t": 0,
                        "e": "UnknownType99",
                        "p": {"data": "ignored"},
                    },
                }
            ]
        )
        builder.apply(response)
        state = builder.build()
        assert len(state.tasks) == 1
        assert "task-1" in state.tasks
