from __future__ import annotations


class ChecklistItemData:
    def __init__(self, title: str, completed: bool = False, cancelled: bool = False):
        self.title = title
        self.completed = completed
        self.cancelled = cancelled


class TaskData:
    def __init__(
        self,
        title: str,
        notes: str = "",
        checklist: list[ChecklistItemData] | None = None,
    ):
        self.title = title
        self.notes = notes
        self.checklist: list[ChecklistItemData] = checklist if checklist else []
