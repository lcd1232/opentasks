from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Union

from .models import (
    ENTITY_TYPE_TO_MODEL,
    Area,
    ChecklistItem,
    HistoryResponse,
    Settings,
    Tag,
    Task,
    TaskType,
    Tombstone,
)

EntityModel = Union[Task, ChecklistItem, Area, Tag, Settings, Tombstone]


@dataclass
class _RawObject:
    entity_type: str
    properties: dict[str, Any]


@dataclass
class StateBuilder:
    _objects: dict[str, _RawObject] = field(default_factory=dict)
    _tombstones: dict[str, Tombstone] = field(default_factory=dict)

    def apply(self, response: HistoryResponse) -> None:
        for item_group in response.items:
            for uuid, obj in item_group.items():
                entity_type = obj.entity_type
                update_type = obj.update_type
                props = obj.properties

                if entity_type == "Tombstone2":
                    self._apply_tombstone(uuid, props)
                elif update_type == 0:
                    self._objects[uuid] = _RawObject(
                        entity_type=entity_type,
                        properties=copy.deepcopy(props),
                    )
                elif update_type == 1:
                    self._apply_delta(uuid, entity_type, props)

    def apply_all(self, responses: list[HistoryResponse]) -> None:
        for response in responses:
            self.apply(response)

    def _apply_delta(self, uuid: str, entity_type: str, delta: dict[str, Any]) -> None:
        if uuid not in self._objects:
            self._objects[uuid] = _RawObject(
                entity_type=entity_type,
                properties=copy.deepcopy(delta),
            )
            return

        existing = self._objects[uuid].properties
        for key, value in delta.items():
            if key == "nt" and isinstance(value, dict) and value.get("t") == 2:
                self._apply_note_patches(existing, value)
            else:
                existing[key] = (
                    copy.deepcopy(value) if isinstance(value, (dict, list)) else value
                )

    @staticmethod
    def _apply_note_patches(
        properties: dict[str, Any], patch_delta: dict[str, Any]
    ) -> None:
        current_nt = properties.get("nt")
        if current_nt is None:
            current_nt = {"_t": "tx", "t": 1, "v": "", "ch": 0}

        text_bytes = current_nt.get("v", "").encode("utf-8")

        for patch in patch_delta.get("ps", []):
            pos = patch.get("p", 0)
            delete_len = patch.get("l", 0)
            replacement = patch.get("r", "").encode("utf-8")
            text_bytes = text_bytes[:pos] + replacement + text_bytes[pos + delete_len :]

        checksum = (
            patch_delta["ps"][-1]["ch"]
            if patch_delta.get("ps")
            else current_nt.get("ch", 0)
        )
        properties["nt"] = {
            "_t": current_nt.get("_t", "tx"),
            "t": 1,
            "v": text_bytes.decode("utf-8"),
            "ch": checksum,
        }

    def _apply_tombstone(self, uuid: str, props: dict[str, Any]) -> None:
        tombstone = Tombstone.from_raw(uuid, props)
        self._tombstones[tombstone.deleted_object_id] = tombstone
        self._objects.pop(tombstone.deleted_object_id, None)

    def build(self) -> State:
        tasks: dict[str, Task] = {}
        checklist_items: dict[str, ChecklistItem] = {}
        areas: dict[str, Area] = {}
        tags: dict[str, Tag] = {}
        settings: dict[str, Settings] = {}

        for uuid, raw in self._objects.items():
            model_cls = ENTITY_TYPE_TO_MODEL.get(raw.entity_type)
            if model_cls is None:
                continue

            obj = model_cls.from_raw(uuid, raw.properties)

            if isinstance(obj, Task):
                tasks[uuid] = obj
            elif isinstance(obj, ChecklistItem):
                checklist_items[uuid] = obj
            elif isinstance(obj, Area):
                areas[uuid] = obj
            elif isinstance(obj, Tag):
                tags[uuid] = obj
            elif isinstance(obj, Settings):
                settings[uuid] = obj

        return State(
            tasks=tasks,
            checklist_items=checklist_items,
            areas=areas,
            tags=tags,
            settings=settings,
            tombstones=dict(self._tombstones),
        )


@dataclass
class State:
    tasks: dict[str, Task] = field(default_factory=dict)
    checklist_items: dict[str, ChecklistItem] = field(default_factory=dict)
    areas: dict[str, Area] = field(default_factory=dict)
    tags: dict[str, Tag] = field(default_factory=dict)
    settings: dict[str, Settings] = field(default_factory=dict)
    tombstones: dict[str, Tombstone] = field(default_factory=dict)

    @property
    def projects(self) -> dict[str, Task]:
        return {uid: t for uid, t in self.tasks.items() if t.is_project}

    @property
    def headings(self) -> dict[str, Task]:
        return {uid: t for uid, t in self.tasks.items() if t.is_heading}

    @property
    def todos(self) -> dict[str, Task]:
        return {
            uid: t
            for uid, t in self.tasks.items()
            if t.task_type == TaskType.TASK and not t.trashed
        }

    @property
    def open_tasks(self) -> dict[str, Task]:
        return {uid: t for uid, t in self.tasks.items() if t.is_open and not t.trashed}

    @property
    def completed_tasks(self) -> dict[str, Task]:
        return {uid: t for uid, t in self.tasks.items() if t.is_completed}

    def tasks_for_project(self, project_id: str) -> list[Task]:
        return sorted(
            [t for t in self.tasks.values() if project_id in t.project_ids],
            key=lambda t: t.index,
        )

    def checklist_for_task(self, task_id: str) -> list[ChecklistItem]:
        return sorted(
            [c for c in self.checklist_items.values() if task_id in c.task_ids],
            key=lambda c: c.index,
        )

    def tasks_for_area(self, area_id: str) -> list[Task]:
        return sorted(
            [t for t in self.tasks.values() if area_id in t.area_ids],
            key=lambda t: t.index,
        )

    def tasks_with_tag(self, tag_id: str) -> list[Task]:
        return sorted(
            [t for t in self.tasks.values() if tag_id in t.tag_ids],
            key=lambda t: t.index,
        )
