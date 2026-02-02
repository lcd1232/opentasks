"""Typed models for Things3 Cloud sync protocol entities."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any

from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class HistoryObject:
    update_type: int = field(metadata=config(field_name="t"))
    entity_type: str = field(metadata=config(field_name="e"))
    properties: dict = field(metadata=config(field_name="p"))


@dataclass_json
@dataclass
class HistoryResponse:
    current_item_index: int = field(metadata=config(field_name="current-item-index"))
    end_total_content_size: int = field(
        metadata=config(field_name="end-total-content-size")
    )
    latest_total_content_size: int = field(
        metadata=config(field_name="latest-total-content-size")
    )
    schema: int = field(metadata=config(field_name="schema"))
    start_total_content_size: int = field(
        metadata=config(field_name="start-total-content-size")
    )
    items: list[dict[str, HistoryObject]] = field(metadata=config(field_name="items"))


@dataclass_json
@dataclass
class AccountInfoResponse:
    sla_version_accepted: str = field(
        metadata=config(field_name="SLA-version-accepted")
    )
    email: str = field(metadata=config(field_name="email"))
    history_key: str = field(metadata=config(field_name="history-key"))
    issues: list = field(metadata=config(field_name="issues"))
    maildrop_email: str | None = field(metadata=config(field_name="maildrop-email"))
    status: str = field(metadata=config(field_name="status"))


class StartType(enum.IntEnum):
    """Task start type (st field)."""

    NOT_STARTED = 0  # Inbox
    ANYTIME = 1  # Started / available
    SOMEDAY = 2  # Deferred / someday


class Status(enum.IntEnum):
    """Object status (ss field)."""

    OPEN = 0
    CANCELLED = 2
    COMPLETED = 3


class TaskType(enum.IntEnum):
    """Task type (tp field)."""

    TASK = 0
    PROJECT = 1
    HEADING = 2


TASK_FIELDS: dict[str, str] = {
    "tt": "title",
    "nt": "notes",
    "st": "start_type",
    "ss": "status",
    "tp": "task_type",
    "cd": "creation_date",
    "md": "modification_date",
    "sp": "stop_date",
    "dd": "deadline",
    "sr": "start_date",
    "tir": "today_index_reference_date",
    "ix": "index",
    "ti": "today_index",
    "pr": "project_ids",
    "agr": "action_group_ids",
    "ar": "area_ids",
    "tg": "tag_ids",
    "rt": "repeating_template_ids",
    "dl": "delegate_ids",
    "tr": "trashed",
    "lt": "logically_trashed",
    "icp": "is_project_completed",
    "icc": "instance_creation_count",
    "icsd": "instance_creation_start_date",
    "dds": "due_date_suppression_date",
    "rmd": "reminder",
    "rr": "recurrence_rule",
    "rp": "repeating_params",
    "ato": "alert_time_offset",
    "lai": "last_alarm_interaction_date",
    "acrd": "action_creation_date",
    "do": "due_order",
    "sb": "subtask_behavior",
    "xx": "extra",
}

CHECKLIST_ITEM_FIELDS: dict[str, str] = {
    "tt": "title",
    "ts": "task_ids",
    "cd": "creation_date",
    "md": "modification_date",
    "sp": "stop_date",
    "ss": "status",
    "ix": "index",
    "lt": "logically_trashed",
    "xx": "extra",
}

AREA_FIELDS: dict[str, str] = {
    "tt": "title",
    "tg": "tag_ids",
    "ix": "index",
    "xx": "extra",
}

TAG_FIELDS: dict[str, str] = {
    "tt": "title",
    "pn": "parent_names",
    "ix": "index",
    "sh": "shortcut",
    "xx": "extra",
}

SETTINGS_FIELDS: dict[str, str] = {
    "grpt": "group_today",
    "ld": "login_date",
    "li": "login_index",
    "usat": "user_settings_account_token",
}

TOMBSTONE_FIELDS: dict[str, str] = {
    "dloid": "deleted_object_id",
    "dld": "deletion_date",
}

FIELD_MAPS: dict[str, dict[str, str]] = {
    "Task6": TASK_FIELDS,
    "ChecklistItem3": CHECKLIST_ITEM_FIELDS,
    "Area3": AREA_FIELDS,
    "Tag4": TAG_FIELDS,
    "Settings5": SETTINGS_FIELDS,
    "Tombstone2": TOMBSTONE_FIELDS,
}


@dataclass
class NoteContent:
    """Represents the structured note text (nt field)."""

    value: str = ""
    checksum: int = 0
    content_type: int = 1
    type_tag: str = "tx"

    @classmethod
    def from_raw(cls, raw: dict[str, Any] | None) -> NoteContent | None:
        if raw is None:
            return None
        return cls(
            value=raw.get("v", ""),
            checksum=raw.get("ch", 0),
            content_type=raw.get("t", 1),
            type_tag=raw.get("_t", "tx"),
        )

    def to_raw(self) -> dict[str, Any]:
        return {
            "v": self.value,
            "ch": self.checksum,
            "t": self.content_type,
            "_t": self.type_tag,
        }


@dataclass
class RecurrenceRule:
    """Represents a recurrence rule (rr field)."""

    start_date: float | None = None  # sr
    initial_after: float | None = None  # ia
    recurrence_count: int = 0  # rc
    end_date: float | None = None  # ed
    frequency_unit: int = 0  # fu
    offsets: list[dict[str, Any]] = field(default_factory=list)  # of
    task_status: int = 0  # ts
    frequency_amount: int = 1  # fa
    recurrence_type: int = 0  # tp
    rule_version: int = 4  # rrv

    @classmethod
    def from_raw(cls, raw: dict[str, Any] | None) -> RecurrenceRule | None:
        if raw is None:
            return None
        return cls(
            start_date=raw.get("sr"),
            initial_after=raw.get("ia"),
            recurrence_count=raw.get("rc", 0),
            end_date=raw.get("ed"),
            frequency_unit=raw.get("fu", 0),
            offsets=raw.get("of", []),
            task_status=raw.get("ts", 0),
            frequency_amount=raw.get("fa", 1),
            recurrence_type=raw.get("tp", 0),
            rule_version=raw.get("rrv", 4),
        )


@dataclass
class Task:
    """A Things3 task, heading, or project (Task6 entity)."""

    uuid: str = ""
    title: str = ""
    notes: NoteContent | None = None
    start_type: StartType = StartType.NOT_STARTED
    status: Status = Status.OPEN
    task_type: TaskType = TaskType.TASK
    creation_date: float | None = None
    modification_date: float | None = None
    stop_date: float | None = None
    deadline: float | None = None
    start_date: float | None = None
    today_index_reference_date: float | None = None
    index: int = 0
    today_index: int = 0
    project_ids: list[str] = field(default_factory=list)
    action_group_ids: list[str] = field(default_factory=list)
    area_ids: list[str] = field(default_factory=list)
    tag_ids: list[str] = field(default_factory=list)
    repeating_template_ids: list[str] = field(default_factory=list)
    delegate_ids: list[str] = field(default_factory=list)
    trashed: bool = False
    logically_trashed: bool = False
    is_project_completed: bool = False
    instance_creation_count: int = 0
    instance_creation_start_date: float | None = None
    due_date_suppression_date: float | None = None
    reminder: float | None = None
    recurrence_rule: RecurrenceRule | None = None
    repeating_params: dict[str, Any] | None = None
    alert_time_offset: float | None = None
    last_alarm_interaction_date: float | None = None
    action_creation_date: float | None = None
    due_order: int = 0
    subtask_behavior: int = 0
    extra: dict[str, Any] | None = None

    @property
    def is_task(self) -> bool:
        return self.task_type == TaskType.TASK

    @property
    def is_project(self) -> bool:
        return self.task_type == TaskType.PROJECT

    @property
    def is_heading(self) -> bool:
        return self.task_type == TaskType.HEADING

    @property
    def is_completed(self) -> bool:
        return self.status == Status.COMPLETED

    @property
    def is_open(self) -> bool:
        return self.status == Status.OPEN

    @classmethod
    def from_raw(cls, uuid: str, props: dict[str, Any]) -> Task:
        return cls(
            uuid=uuid,
            title=props.get("tt", ""),
            notes=NoteContent.from_raw(props.get("nt")),
            start_type=StartType(props.get("st", 0)),
            status=Status(props.get("ss", 0)),
            task_type=TaskType(props.get("tp", 0)),
            creation_date=props.get("cd"),
            modification_date=props.get("md"),
            stop_date=props.get("sp"),
            deadline=props.get("dd"),
            start_date=props.get("sr"),
            today_index_reference_date=props.get("tir"),
            index=props.get("ix", 0),
            today_index=props.get("ti", 0),
            project_ids=props.get("pr", []),
            action_group_ids=props.get("agr", []),
            area_ids=props.get("ar", []),
            tag_ids=props.get("tg", []),
            repeating_template_ids=props.get("rt", []),
            delegate_ids=props.get("dl", []),
            trashed=props.get("tr", False),
            logically_trashed=props.get("lt", False),
            is_project_completed=props.get("icp", False),
            instance_creation_count=props.get("icc", 0),
            instance_creation_start_date=props.get("icsd"),
            due_date_suppression_date=props.get("dds"),
            reminder=props.get("rmd"),
            recurrence_rule=RecurrenceRule.from_raw(props.get("rr")),
            repeating_params=props.get("rp"),
            alert_time_offset=props.get("ato"),
            last_alarm_interaction_date=props.get("lai"),
            action_creation_date=props.get("acrd"),
            due_order=props.get("do", 0),
            subtask_behavior=props.get("sb", 0),
            extra=props.get("xx"),
        )


@dataclass
class ChecklistItem:
    """A Things3 checklist item (ChecklistItem3 entity)."""

    uuid: str = ""
    title: str = ""
    task_ids: list[str] = field(default_factory=list)
    creation_date: float | None = None
    modification_date: float | None = None
    stop_date: float | None = None
    status: Status = Status.OPEN
    index: int = 0
    logically_trashed: bool = False
    extra: dict[str, Any] | None = None

    @property
    def is_completed(self) -> bool:
        return self.status == Status.COMPLETED

    @classmethod
    def from_raw(cls, uuid: str, props: dict[str, Any]) -> ChecklistItem:
        return cls(
            uuid=uuid,
            title=props.get("tt", ""),
            task_ids=props.get("ts", []),
            creation_date=props.get("cd"),
            modification_date=props.get("md"),
            stop_date=props.get("sp"),
            status=Status(props.get("ss", 0)),
            index=props.get("ix", 0),
            logically_trashed=props.get("lt", False),
            extra=props.get("xx"),
        )


@dataclass
class Area:
    """A Things3 area (Area3 entity)."""

    uuid: str = ""
    title: str = ""
    tag_ids: list[str] = field(default_factory=list)
    index: int = 0
    extra: dict[str, Any] | None = None

    @classmethod
    def from_raw(cls, uuid: str, props: dict[str, Any]) -> Area:
        return cls(
            uuid=uuid,
            title=props.get("tt", ""),
            tag_ids=props.get("tg", []),
            index=props.get("ix", 0),
            extra=props.get("xx"),
        )


@dataclass
class Tag:
    """A Things3 tag (Tag4 entity)."""

    uuid: str = ""
    title: str = ""
    parent_names: list[str] = field(default_factory=list)
    index: int = 0
    shortcut: str | None = None
    extra: dict[str, Any] | None = None

    @classmethod
    def from_raw(cls, uuid: str, props: dict[str, Any]) -> Tag:
        return cls(
            uuid=uuid,
            title=props.get("tt", ""),
            parent_names=props.get("pn", []),
            index=props.get("ix", 0),
            shortcut=props.get("sh"),
            extra=props.get("xx"),
        )


@dataclass
class Settings:
    """Things3 settings (Settings5 entity)."""

    uuid: str = ""
    group_today: bool = False
    login_date: float | None = None
    login_index: int = 0
    user_settings_account_token: str | None = None

    @classmethod
    def from_raw(cls, uuid: str, props: dict[str, Any]) -> Settings:
        return cls(
            uuid=uuid,
            group_today=props.get("grpt", False),
            login_date=props.get("ld"),
            login_index=props.get("li", 0),
            user_settings_account_token=props.get("usat"),
        )


@dataclass
class Tombstone:
    """A Things3 tombstone — marks a deleted object (Tombstone2 entity)."""

    uuid: str = ""
    deleted_object_id: str = ""
    deletion_date: float | None = None

    @classmethod
    def from_raw(cls, uuid: str, props: dict[str, Any]) -> Tombstone:
        return cls(
            uuid=uuid,
            deleted_object_id=props.get("dloid", ""),
            deletion_date=props.get("dld"),
        )


ENTITY_TYPE_TO_MODEL: dict[str, type] = {
    "Task6": Task,
    "ChecklistItem3": ChecklistItem,
    "Area3": Area,
    "Tag4": Tag,
    "Settings5": Settings,
    "Tombstone2": Tombstone,
}
